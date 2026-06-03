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

import redis.asyncio as aioredis
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Response, status

from app.core.config import get_settings
from app.core.dependencies import (  # ← single import source, always
    AuthServiceDep,
    CurrentUser,
    EmailVerifServiceDep,
    PasswordResetServiceDep,
    RedisDep,
)
from app.core.exceptions import (
    AccountDisabledError,
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
    VerifyEmailResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


def _set_refresh_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key="lingvopal_rt",
        value=token,
        httponly=True,
        secure=settings.is_production,
        samesite="strict" if settings.is_production else "lax",
        path="/api/v1/auth",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key="lingvopal_rt", path="/api/v1/auth")


# ============================================================================
# EXCEPTION → HTTP STATUS MAP
# One place to maintain the mapping; keeps route handlers thin.
# ============================================================================

_AUTH_ERROR_STATUS: dict[type[AuthError], int] = {
    InvalidCredentialsError: status.HTTP_401_UNAUTHORIZED,
    AccountDisabledError: status.HTTP_403_FORBIDDEN,
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


async def _send_password_reset_background(user_id: int, email: str, redis: aioredis.Redis) -> None:
    # redis is the already-resolved client forwarded from the route — not injected by FastAPI.
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


async def _send_verification_background(user_id: int, email: str, redis: aioredis.Redis) -> None:
    # redis is the already-resolved client forwarded from the route — not injected by FastAPI.
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
    response: Response,
    body: SignupRequest,
    auth: AuthServiceDep,
    redis: RedisDep,
    background_tasks: BackgroundTasks,
) -> TokenResponse:
    try:
        result = await auth.signup(body, accept_language=request.headers.get("Accept-Language"))
        _set_refresh_cookie(response, result.refresh_token)
        background_tasks.add_task(
            _send_verification_background,
            user_id=result.user.id,
            email=result.user.email,
            redis=redis,
        )
        return result
    except (EmailAlreadyExistsError, UsernameAlreadyExistsError) as exc:
        _handle_auth_error(exc)


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
    response: Response,
    body: LoginRequest,
    auth: AuthServiceDep,
) -> TokenResponse:
    client_ip = request.client.host if request.client else None
    try:
        result = await auth.login(body, client_ip=client_ip)
        _set_refresh_cookie(response, result.refresh_token)
        return result
    except (InvalidCredentialsError, AccountDisabledError) as exc:
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
) -> VerifyEmailResponse:
    try:
        user_id = await email_verif.consume_token(body.token)
        await auth.mark_email_verified(user_id)
        return VerifyEmailResponse(message="Email verified successfully.")
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
    user = await auth.get_user_by_email(body.email)
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
    response: Response,
    auth: AuthServiceDep,
    body: RefreshRequest | None = None,
) -> RefreshResponse:
    token = request.cookies.get("lingvopal_rt") or (body.refresh_token if body else None)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "refresh_token_invalid", "message": "No refresh token provided."},
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        result = await auth.refresh(token)
        _set_refresh_cookie(response, result.refresh_token)
        return result
    except RefreshTokenInvalidError as exc:
        _clear_refresh_cookie(response)
        _handle_auth_error(exc)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout — revokes refresh token",
)
async def logout(current_user: CurrentUser, auth: AuthServiceDep, response: Response) -> None:
    await auth.revoke_refresh_token(current_user.id)
    _clear_refresh_cookie(response)
