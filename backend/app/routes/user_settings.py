# backend/app/routes/user_settings.py
"""
User settings routes — HTTP layer only.

Rules:
  - Parse request, call service, map domain exceptions to HTTP responses.
  - Zero business logic here.
"""

from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import CurrentUser, UserSettingsServiceDep
from app.core.exceptions import SettingsValidationError
from app.schemas.user_settings import UserSettingsPatchRequest, UserSettingsResponse

router = APIRouter(prefix="/settings", tags=["settings"])


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.get(
    "/me",
    response_model=UserSettingsResponse,
    summary="Get current user's settings",
)
async def get_my_settings(
    current_user: CurrentUser,
    svc: UserSettingsServiceDep,
) -> UserSettingsResponse:
    """Return the authenticated user's full settings (auto-creates with defaults if missing)."""
    settings = await svc.get_or_create(current_user.id)
    return UserSettingsResponse.model_validate(settings)


@router.patch(
    "/me",
    response_model=UserSettingsResponse,
    summary="Partially update current user's settings",
    responses={
        422: {"description": "Settings validation failed"},
    },
)
async def patch_my_settings(
    body: UserSettingsPatchRequest,
    current_user: CurrentUser,
    svc: UserSettingsServiceDep,
) -> UserSettingsResponse:
    """
    Update only the fields provided in the request body.
    Unset fields are left unchanged.
    """
    patch_data = body.model_dump(exclude_unset=True)

    if not patch_data:
        # Nothing to update — return current settings unchanged.
        settings = await svc.get_or_create(current_user.id)
        return UserSettingsResponse.model_validate(settings)

    try:
        settings = await svc.update_settings(current_user.id, patch_data)
    except SettingsValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"field": exc.field, "message": exc.reason},
        )

    return UserSettingsResponse.model_validate(settings)


@router.post(
    "/reset",
    response_model=UserSettingsResponse,
    summary="Reset settings to defaults",
    responses={
        200: {"description": "Settings reset to defaults successfully"},
    },
)
async def reset_my_settings(
    current_user: CurrentUser,
    svc: UserSettingsServiceDep,
) -> UserSettingsResponse:
    """Reset all preference fields to their default values (language settings are preserved)."""
    settings = await svc.reset_settings(current_user.id)
    return UserSettingsResponse.model_validate(settings)
