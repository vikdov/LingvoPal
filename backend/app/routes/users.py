# backend/app/routes/users.py
"""
User profile routes.

Covers the authenticated user's own profile management.
Admin management of other users lives in routes/admin.py.
"""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, update

from app.core.dependencies import CurrentUser, DBSession, VerifiedUser
from app.models.user import User
from app.schemas.user import UserPrivateResponse, UserUpdateRequest

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserPrivateResponse,
    summary="Get current user's profile",
)
async def get_my_profile(current_user: CurrentUser) -> UserPrivateResponse:
    """Return the authenticated user's profile."""
    return UserPrivateResponse.model_validate(current_user)


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
    """
    Update the authenticated user's mutable profile fields.

    Currently only `username` is patchable.
    Email changes require a separate verification flow (not implemented here).
    """
    patch = body.model_dump(exclude_unset=True)
    if not patch:
        return UserPrivateResponse.model_validate(current_user)

    if "username" in patch and patch["username"] is not None:
        # Check uniqueness
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
    return UserPrivateResponse.model_validate(refreshed)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete current user's account",
)
async def delete_my_account(
    current_user: VerifiedUser,
    db: DBSession,
) -> None:
    """
    Soft-delete the authenticated user's account.

    Sets deleted_at; does not purge data. The account cannot log in
    after this point. Data is retained for audit purposes.
    """
    from datetime import datetime, timezone

    await db.execute(
        update(User)
        .where(User.id == current_user.id)
        .values(deleted_at=datetime.now(timezone.utc))
    )
    await db.commit()
