# backend/app/schemas/__init__.py
"""
Central schema exports.

All schemas exported here for easy importing:
    from app.schemas import UserPrivateResponse, ItemDetailResponse
"""

# Common
from app.schemas.common import (
    BaseResponse,
    BaseResponseWithUpdated,
    BaseResponseWithDeleted,
    PaginatedResponse,
    ErrorResponse,
    ErrorDetail,
    ListQueryParams,
)

# Auth
from app.schemas.auth import (
    SignupRequest,
    LoginRequest,
    PasswordChangeRequest,
    TokenResponse,
    AuthErrorResponse,
)

# User
from app.schemas.user import (
    UserUpdateRequest,
    UserSettingsUpdateRequest,
    UserPublicResponse,
    UserPrivateResponse,
    UserDetailResponse,
    UserSettingsResponse,
    LanguageRefResponse,
)

# Language (read-only reference)
from app.schemas.language import LanguageResponse

# Items
from app.schemas.item import (
    ItemBase,
    ItemCreateRequest,
    ItemUpdateRequest,
    ItemListResponse,
    ItemResponse,
    ItemDetailResponse,
    TranslationCreateRequest,
    TranslationResponse,
    ItemListQueryParams,
)

# Sets
from app.schemas.set import (
    SetBase,
    SetCreateRequest,
    SetUpdateRequest,
    SetListResponse,
    SetResponse,
    SetDetailResponse,
    SetItemReference,
    SetListQueryParams,
)

# Practice
from app.schemas.practice import (
    StartStudySessionRequest,
    SubmitReviewRequest,
    QuestionResponse,
    StudyReviewResponse,
    StudySessionResponse,
    StudySessionDetailResponse,
    SessionHistoryQueryParams,
)

# Stats
from app.schemas.stats import (
    DailyStatsResponse,
    TotalStatsResponse,
    StatsRangeResponse,
    StatsRangeQueryParams,
    DailyStatsQueryParams,
)

# Moderation
from app.schemas.moderation import (
    ApproveModerationRequest,
    RejectModerationRequest,
    PendingModerationResponse,
)

# Admin
from app.schemas.admin import (
    UserListQueryParams,
    RepairStatsRequest,
)

__all__ = [
    # Common
    "BaseResponse",
    "BaseResponseWithUpdated",
    "BaseResponseWithDeleted",
    "PaginatedResponse",
    "ErrorResponse",
    "ErrorDetail",
    "ListQueryParams",
    # Auth
    "SignupRequest",
    "LoginRequest",
    "PasswordChangeRequest",
    "TokenResponse",
    "AuthErrorResponse",
    # User
    "UserUpdateRequest",
    "UserSettingsUpdateRequest",
    "UserPublicResponse",
    "UserPrivateResponse",
    "UserDetailResponse",
    "UserSettingsResponse",
    "LanguageRefResponse",
    # Language
    "LanguageResponse",
    # Items
    "ItemBase",
    "ItemCreateRequest",
    "ItemUpdateRequest",
    "ItemListResponse",
    "ItemResponse",
    "ItemDetailResponse",
    "TranslationCreateRequest",
    "TranslationResponse",
    "ItemListQueryParams",
    # Sets
    "SetBase",
    "SetCreateRequest",
    "SetUpdateRequest",
    "SetListResponse",
    "SetResponse",
    "SetDetailResponse",
    "SetItemReference",
    "SetListQueryParams",
    # Practice
    "StartStudySessionRequest",
    "SubmitReviewRequest",
    "QuestionResponse",
    "StudyReviewResponse",
    "StudySessionResponse",
    "StudySessionDetailResponse",
    "SessionHistoryQueryParams",
    # Stats
    "DailyStatsResponse",
    "TotalStatsResponse",
    "StatsRangeResponse",
    "StatsRangeQueryParams",
    "DailyStatsQueryParams",
    # Moderation
    "ApproveModerationRequest",
    "RejectModerationRequest",
    "PendingModerationResponse",
    # Admin
    "UserListQueryParams",
    "RepairStatsRequest",
]
