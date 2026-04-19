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
    UserPublicResponse,
    UserPrivateResponse,
    UserDetailResponse,
    UserSettingsEmbedded,
    LanguageRefResponse,
)

# Language (read-only reference)
from app.schemas.language import LanguageResponse

# Items
from app.schemas.item import (
    ItemCreateRequest,
    ItemUpdateRequest,
    AddExistingItemRequest,
    ItemResponse,
    SetItemResponse,
    ItemDetailResponse,
    TranslationCreateRequest,
    TranslationResponse,
)

# Sets
from app.schemas.set import (
    SetCreateRequest,
    SetUpdateRequest,
    SetResponse,
    SetDetailResponse,
    SetLibraryEntryResponse,
)

# Practice
from app.schemas.practice import (
    ComparisonConfig,
    ItemHintSchema,
    StartSessionRequest,
    SessionStartedResponse,
    SubmitAnswerRequest,
    AnswerBufferedResponse,
    SessionSummaryResponse,
    ActiveSessionResponse,
)

# Stats
from app.schemas.stats import (
    DailyStatsResponse,
    TotalStatsResponse,
    StatsRangeResponse,
    StatsRangeQueryParams,
    DailyStatsQueryParams,
    HardestItemResponse,
)

# User settings
from app.schemas.user_settings import (
    UserSettingsResponse,
    UserSettingsPatchRequest,
)

# Moderation
from app.schemas.moderation import (
    SubmitForReviewRequest,
    ApproveModerationRequest,
    RejectModerationRequest,
    ModerationListQueryParams,
    ModerationSubmissionResponse,
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
    "UserPublicResponse",
    "UserPrivateResponse",
    "UserDetailResponse",
    "UserSettingsEmbedded",
    "LanguageRefResponse",
    # Language
    "LanguageResponse",
    # Items
    "ItemCreateRequest",
    "ItemUpdateRequest",
    "AddExistingItemRequest",
    "ItemResponse",
    "SetItemResponse",
    "ItemDetailResponse",
    "TranslationCreateRequest",
    "TranslationResponse",
    # Sets
    "SetCreateRequest",
    "SetUpdateRequest",
    "SetResponse",
    "SetDetailResponse",
    "SetLibraryEntryResponse",
    # Practice
    "ComparisonConfig",
    "ItemHintSchema",
    "StartSessionRequest",
    "SessionStartedResponse",
    "SubmitAnswerRequest",
    "AnswerBufferedResponse",
    "SessionSummaryResponse",
    "ActiveSessionResponse",
    # Stats
    "DailyStatsResponse",
    "TotalStatsResponse",
    "StatsRangeResponse",
    "StatsRangeQueryParams",
    "DailyStatsQueryParams",
    "HardestItemResponse",
    # User settings
    "UserSettingsResponse",
    "UserSettingsPatchRequest",
    # Moderation
    "SubmitForReviewRequest",
    "ApproveModerationRequest",
    "RejectModerationRequest",
    "ModerationListQueryParams",
    "ModerationSubmissionResponse",
    "PendingModerationResponse",
    # Admin
    "UserListQueryParams",
    "RepairStatsRequest",
]
