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

from typing import NoReturn

from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import (  # ← single import source, always
    AuthServiceDep,
    CurrentUser,
)
from app.core.exceptions import (
    AuthError,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    SamePasswordError,
    UsernameAlreadyExistsError,
)
from app.schemas.auth import (
    AuthErrorResponse,
    LoginRequest,
    PasswordChangeRequest,
    SignupRequest,
    TokenResponse,
)

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
}


def _handle_auth_error(exc: AuthError) -> NoReturn:
    """Convert a domain AuthError into the appropriate HTTPException."""
    http_status = _AUTH_ERROR_STATUS.get(type(exc), status.HTTP_400_BAD_REQUEST)
    headers = (
        {"WWW-Authenticate": "Bearer"}
        if http_status == status.HTTP_401_UNAUTHORIZED
        else None
    )
    raise HTTPException(
        status_code=http_status,
        detail=AuthErrorResponse(error=exc.code, message=exc.message).model_dump(),
        headers=headers,
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
async def signup(
    body: SignupRequest,
    auth: AuthServiceDep,
) -> TokenResponse:
    try:
        return await auth.signup(body)
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
async def login(
    body: LoginRequest,
    auth: AuthServiceDep,
) -> TokenResponse:
    try:
        return await auth.login(body)
    except InvalidCredentialsError as exc:
        _handle_auth_error(exc)


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
async def change_password(
    body: PasswordChangeRequest,
    auth: AuthServiceDep,
    current_user: CurrentUser,
) -> None:
    try:
        await auth.change_password(current_user.id, body)
    except (InvalidCredentialsError, SamePasswordError) as exc:
        _handle_auth_error(exc)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout (client-side token discard)",
)
async def logout(current_user: CurrentUser) -> None:
    """
    Stateless JWT logout — the client discards the token.
    If you add a Redis token denylist later, invalidate here.
    The dependency validates the token is still good before we get here.
    """
    return None
