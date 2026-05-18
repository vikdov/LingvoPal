# backend/app/routes/users.py
"""
User profile routes.

Covers the authenticated user's own profile management.
Admin management of other users lives in routes/admin.py.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    CurrentUser,
    DBSession,
    EmailChangeServiceDep,
    EmailServiceDep,
    VerifiedUser,
)
from app.core.exceptions import (
    DuplicateResourceError,
    EmailChangeTokenInvalidError,
    ResourceNotFoundError,
)
from app.models.user import User
from app.repositories.user_language_repo import UserLanguageRepository
from app.schemas.user import UserPrivateResponse, UserUpdateRequest
from app.schemas.user_language import (
    AddUserLanguageRequest,
    UserLanguageResponse,
    UserLanguagesResponse,
)
from app.services.user_language_service import UserLanguageService
from app.services.user_settings_service import UserSettingsService

router = APIRouter(prefix="/users", tags=["users"])


async def _build_user_response(user: User, db: AsyncSession) -> UserPrivateResponse:
    settings = await UserSettingsService(db).get_or_create(user.id)
    active_lang_id = await UserLanguageRepository(db).get_active_lang_id(user.id)
    return UserPrivateResponse(
        id=user.id,
        created_at=user.created_at,
        username=user.username,
        email=user.email,
        email_verified=user.email_verified,
        pending_email=user.pending_email,
        is_admin=user.is_admin,
        native_lang_id=settings.native_lang_id,
        active_target_lang_id=active_lang_id,
    )


@router.get(
    "/me",
    response_model=UserPrivateResponse,
    summary="Get current user's profile",
)
async def get_my_profile(current_user: CurrentUser, db: DBSession) -> UserPrivateResponse:
    return await _build_user_response(current_user, db)


@router.patch(
    "/me",
    response_model=UserPrivateResponse,
    summary="Update current user's profile",
)
async def patch_my_profile(
    body: UserUpdateRequest,
    current_user: VerifiedUser,
    db: DBSession,
) -> UserPrivateResponse:
    patch = body.model_dump(exclude_unset=True)
    if not patch:
        return await _build_user_response(current_user, db)

    if "username" in patch and patch["username"] is not None:
        existing = await db.scalar(
            select(User.id).where(
                User.username == patch["username"],
                User.id != current_user.id,
            )
        )
        if existing is not None:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail="This username is already taken.",
            )

    await db.execute(update(User).where(User.id == current_user.id).values(**patch))
    await db.commit()

    refreshed = await db.get(User, current_user.id)
    return await _build_user_response(refreshed, db)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete current user's account",
)
async def delete_my_account(
    current_user: VerifiedUser,
    db: DBSession,
) -> None:
    from datetime import datetime, timezone

    await db.execute(
        update(User)
        .where(User.id == current_user.id)
        .values(deleted_at=datetime.now(timezone.utc))
    )
    await db.commit()


# ============================================================================
# LANGUAGE MANAGEMENT
# ============================================================================


@router.get(
    "/me/languages",
    response_model=UserLanguagesResponse,
    summary="Get all languages the current user is learning",
)
async def get_my_languages(
    current_user: CurrentUser,
    db: DBSession,
) -> UserLanguagesResponse:
    svc = UserLanguageService(db)
    rows = await svc.get_all(current_user.id)
    active = next((r.language for r in rows if r.is_active), None)
    return UserLanguagesResponse(
        languages=[UserLanguageResponse.model_validate(r) for r in rows],
        active_language=active,
    )


@router.post(
    "/me/languages",
    response_model=UserLanguageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a language to the current user's learning list",
)
async def add_my_language(
    body: AddUserLanguageRequest,
    current_user: VerifiedUser,
    db: DBSession,
) -> UserLanguageResponse:
    svc = UserLanguageService(db)
    try:
        row = await svc.add_language(
            current_user.id,
            body.language_id,
            set_active=body.set_active,
        )
    except ResourceNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Language not found.")
    except DuplicateResourceError:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="You are already learning this language.",
        )
    return UserLanguageResponse.model_validate(row)


@router.post(
    "/me/languages/{language_id}/activate",
    response_model=UserLanguageResponse,
    summary="Switch the active learning language",
)
async def activate_my_language(
    language_id: int,
    current_user: VerifiedUser,
    db: DBSession,
) -> UserLanguageResponse:
    svc = UserLanguageService(db)
    try:
        row = await svc.activate_language(current_user.id, language_id)
    except ResourceNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Language not in your learning list.",
        )
    return UserLanguageResponse.model_validate(row)


@router.delete(
    "/me/languages/{language_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a language from the current user's learning list",
)
async def remove_my_language(
    language_id: int,
    current_user: VerifiedUser,
    db: DBSession,
) -> None:
    svc = UserLanguageService(db)
    try:
        await svc.remove_language(current_user.id, language_id)
    except ResourceNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Language not in your learning list.",
        )


# ============================================================================
# EMAIL CHANGE
# ============================================================================


class EmailChangeRequest(BaseModel):
    new_email: EmailStr


class EmailChangeConfirmRequest(BaseModel):
    token: str


@router.post(
    "/me/email-change",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Request an email address change",
)
async def request_email_change(
    body: EmailChangeRequest,
    current_user: VerifiedUser,
    db: DBSession,
    email_change_svc: EmailChangeServiceDep,
    email_svc: EmailServiceDep,
) -> None:
    new_email = str(body.new_email).lower()
    if new_email == current_user.email.lower():
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="New email is the same as your current email.",
        )

    taken = await db.scalar(
        select(User.id).where(
            User.email == new_email,
            User.id != current_user.id,
            User.deleted_at.is_(None),
        )
    )
    if taken is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="This email address is already in use.",
        )

    token = await email_change_svc.generate_token(current_user.id, new_email)
    await db.execute(update(User).where(User.id == current_user.id).values(pending_email=new_email))
    await db.commit()

    try:
        await email_svc.send_email_change_verification(new_email, token)
    except Exception:
        pass


@router.post(
    "/me/email-change/confirm",
    response_model=UserPrivateResponse,
    summary="Confirm email change via token (public — no auth required)",
)
async def confirm_email_change(
    body: EmailChangeConfirmRequest,
    db: DBSession,
    email_change_svc: EmailChangeServiceDep,
) -> UserPrivateResponse:
    try:
        user_id, new_email = await email_change_svc.consume_token(body.token)
    except EmailChangeTokenInvalidError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={"error": "email_change_token_invalid", "message": "Email change token is invalid or has expired."},
        )

    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(email=new_email, pending_email=None, email_verified=True)
    )
    await db.commit()

    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found.")
    return await _build_user_response(user, db)


@router.delete(
    "/me/email-change",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel pending email change",
)
async def cancel_email_change(
    current_user: VerifiedUser,
    db: DBSession,
    email_change_svc: EmailChangeServiceDep,
) -> None:
    await email_change_svc.cancel_token(current_user.id)
    await db.execute(update(User).where(User.id == current_user.id).values(pending_email=None))
    await db.commit()
