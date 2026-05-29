# backend/app/routes/auth.py
"""
Auth routes — HTTP concerns only.

Rules:
  - Parse validated request body (Pydantic does this)
  - Call service method
  - Map domain exceptions → HTTP responses
  - Return typed response schema
  - Zero business logic here
"""

import logging
from typing import NoReturn

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status

from app.core.config import get_settings
from app.core.dependencies import (  # ← single import source, always
    AuthServiceDep,
    CurrentUser,
    EmailVerifServiceDep,
    PasswordResetServiceDep,
    RedisDep,
)
from app.core.exceptions import (
    AlreadyVerifiedError,
    AuthError,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    PasswordResetTokenInvalidError,
    RefreshTokenInvalidError,
    SamePasswordError,
    UsernameAlreadyExistsError,
    VerificationRateLimitedError,
    VerificationTokenInvalidError,
)
from app.core.limiter import auth_rate_limit
from app.schemas.auth import (
    AuthErrorResponse,
    ForgotPasswordRequest,
    LoginRequest,
    PasswordChangeRequest,
    RefreshRequest,
    RefreshResponse,
    ResetPasswordRequest,
    SignupRequest,
    TokenResponse,
    VerifyEmailRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


# ============================================================================
# EXCEPTION → HTTP STATUS MAP
# One place to maintain the mapping; keeps route handlers thin.
# ============================================================================

_AUTH_ERROR_STATUS: dict[type[AuthError], int] = {
    InvalidCredentialsError: status.HTTP_401_UNAUTHORIZED,
    EmailAlreadyExistsError: status.HTTP_409_CONFLICT,
    UsernameAlreadyExistsError: status.HTTP_409_CONFLICT,
    SamePasswordError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    VerificationTokenInvalidError: status.HTTP_400_BAD_REQUEST,
    AlreadyVerifiedError: status.HTTP_409_CONFLICT,
    VerificationRateLimitedError: status.HTTP_429_TOO_MANY_REQUESTS,
    PasswordResetTokenInvalidError: status.HTTP_400_BAD_REQUEST,
    RefreshTokenInvalidError: status.HTTP_401_UNAUTHORIZED,
}


def _handle_auth_error(exc: AuthError) -> NoReturn:
    """Convert a domain AuthError into the appropriate HTTPException."""
    http_status = _AUTH_ERROR_STATUS.get(type(exc), status.HTTP_400_BAD_REQUEST)
    headers = (
        {"WWW-Authenticate": "Bearer"} if http_status == status.HTTP_401_UNAUTHORIZED else None
    )
    raise HTTPException(
        status_code=http_status,
        detail=AuthErrorResponse(error=exc.code, message=exc.message).model_dump(),
        headers=headers,
    )


# ============================================================================
# BACKGROUND TASK
# Primitives only — no request-scoped services passed in.
# Fresh service instances are created inside to avoid lifecycle bugs.
# ============================================================================


async def _send_password_reset_background(user_id: int, email: str, redis: RedisDep) -> None:
    from app.services.email_service import EmailService
    from app.services.password_reset_service import PasswordResetService

    try:
        token = await PasswordResetService(redis).generate_token(user_id)
        await EmailService(get_settings()).send_password_reset(email, token)
    except Exception as exc:
        logger.warning(
            "password_reset_email_failed",
            extra={"user_id": user_id, "email": email, "error": str(exc)},
        )


async def _send_verification_background(user_id: int, email: str, redis: RedisDep) -> None:
    from app.services.email_service import EmailService
    from app.services.email_verification_service import EmailVerificationService

    try:
        token = await EmailVerificationService(redis).generate_token(user_id)
        await EmailService(get_settings()).send_verification(email, token)
    except Exception as exc:
        logger.warning(
            "verification_email_failed",
            extra={"user_id": user_id, "email": email, "error": str(exc)},
        )


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post(
    "/signup",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new account",
    responses={
        409: {
            "model": AuthErrorResponse,
            "description": "Email or username already exists",
        },
    },
)
@auth_rate_limit("5/minute")
async def signup(
    request: Request,
    body: SignupRequest,
    auth: AuthServiceDep,
    redis: RedisDep,
    background_tasks: BackgroundTasks,
) -> TokenResponse:
    try:
        response = await auth.signup(body, accept_language=request.headers.get("Accept-Language"))
    except (EmailAlreadyExistsError, UsernameAlreadyExistsError) as exc:
        _handle_auth_error(exc)

    background_tasks.add_task(
        _send_verification_background,
        user_id=response.user.id,
        email=response.user.email,
        redis=redis,
    )
    return response


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email and password",
    responses={
        401: {"model": AuthErrorResponse, "description": "Invalid credentials"},
    },
)
@auth_rate_limit("10/minute")
async def login(
    request: Request,
    body: LoginRequest,
    auth: AuthServiceDep,
) -> TokenResponse:
    try:
        return await auth.login(body)
    except InvalidCredentialsError as exc:
        _handle_auth_error(exc)


@router.post(
    "/verify-email",
    summary="Verify email address via token from email link",
    responses={
        400: {"model": AuthErrorResponse, "description": "Token invalid or expired"},
        409: {"model": AuthErrorResponse, "description": "Already verified"},
    },
)
async def verify_email(
    body: VerifyEmailRequest,
    auth: AuthServiceDep,
    email_verif: EmailVerifServiceDep,
) -> dict:
    try:
        user_id = await email_verif.consume_token(body.token)
        await auth.mark_email_verified(user_id)
        return {"message": "Email verified successfully."}
    except (VerificationTokenInvalidError, AlreadyVerifiedError) as exc:
        _handle_auth_error(exc)


@router.post(
    "/resend-verification",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Resend verification email (max 5/day, 1/minute)",
    responses={
        409: {"model": AuthErrorResponse, "description": "Already verified"},
        429: {"model": AuthErrorResponse, "description": "Daily limit reached"},
    },
)
@auth_rate_limit("1/minute")
async def resend_verification(
    request: Request,
    current_user: CurrentUser,
    email_verif: EmailVerifServiceDep,
    redis: RedisDep,
    background_tasks: BackgroundTasks,
) -> None:
    try:
        if current_user.email_verified:
            raise AlreadyVerifiedError()
        await email_verif.check_and_increment_daily(current_user.id)
    except (AlreadyVerifiedError, VerificationRateLimitedError) as exc:
        _handle_auth_error(exc)

    background_tasks.add_task(
        _send_verification_background,
        user_id=current_user.id,
        email=current_user.email,
        redis=redis,
    )


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change password for the authenticated user",
    responses={
        401: {"model": AuthErrorResponse, "description": "Current password wrong"},
        422: {
            "model": AuthErrorResponse,
            "description": "New password same as current",
        },
    },
)
@auth_rate_limit("5/minute")
async def change_password(
    request: Request,
    body: PasswordChangeRequest,
    auth: AuthServiceDep,
    current_user: CurrentUser,
) -> None:
    try:
        await auth.change_password(current_user.id, body)
    except (InvalidCredentialsError, SamePasswordError) as exc:
        _handle_auth_error(exc)


@router.post(
    "/forgot-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Request a password reset email",
)
@auth_rate_limit("5/minute")
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    auth: AuthServiceDep,
    redis: RedisDep,
    background_tasks: BackgroundTasks,
) -> None:
    """
    Always returns 204 — never reveals whether the email exists.
    Reset email is sent in a background task.
    """
    from app.repositories.user_repo import UserRepository

    user = await UserRepository(auth._session).get_by_email(body.email)
    if user:
        background_tasks.add_task(
            _send_password_reset_background,
            user_id=user.id,
            email=user.email,
            redis=redis,
        )


@router.post(
    "/reset-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reset password using token from email",
    responses={
        400: {
            "model": AuthErrorResponse,
            "description": "Token invalid or expired",
        },
    },
)
async def reset_password(
    body: ResetPasswordRequest,
    auth: AuthServiceDep,
    pwd_reset: PasswordResetServiceDep,
) -> None:
    try:
        user_id = await pwd_reset.consume_token(body.token)
        await auth.reset_password(user_id, body.new_password)
    except (PasswordResetTokenInvalidError, VerificationTokenInvalidError) as exc:
        _handle_auth_error(exc)


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    summary="Refresh access token using a refresh token",
    responses={
        401: {"model": AuthErrorResponse, "description": "Refresh token invalid or expired"},
    },
)
@auth_rate_limit("20/minute")
async def refresh_token(
    request: Request,
    body: RefreshRequest,
    auth: AuthServiceDep,
) -> RefreshResponse:
    try:
        return await auth.refresh(body.refresh_token)
    except RefreshTokenInvalidError as exc:
        _handle_auth_error(exc)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout — revokes refresh token",
)
async def logout(current_user: CurrentUser, auth: AuthServiceDep) -> None:
    await auth.revoke_refresh_token(current_user.id)
    return None
