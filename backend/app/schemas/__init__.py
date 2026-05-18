# backend/app/schemas/__init__.py
"""
Central schema exports.

All schemas exported here for easy importing:
    from app.schemas import UserPrivateResponse, ItemDetailResponse
"""

# Common
# Admin
from app.schemas.admin import (
    RepairStatsRequest,
    UserListQueryParams,
)

# Auth
from app.schemas.auth import (
    AuthErrorResponse,
    LoginRequest,
    PasswordChangeRequest,
    SignupRequest,
    TokenResponse,
)
from app.schemas.common import (
    BaseResponse,
    BaseResponseWithDeleted,
    BaseResponseWithUpdated,
    ErrorDetail,
    ErrorResponse,
    ListQueryParams,
    PaginatedResponse,
)

# Items
from app.schemas.item import (
    AddExistingItemRequest,
    ItemCreateRequest,
    ItemDetailResponse,
    ItemResponse,
    ItemUpdateRequest,
    SetItemResponse,
    TranslationCreateRequest,
    TranslationResponse,
)

# Language (read-only reference)
from app.schemas.language import LanguageResponse

# Moderation
from app.schemas.moderation import (
    ApproveModerationRequest,
    ModerationListQueryParams,
    ModerationSubmissionResponse,
    PendingModerationResponse,
    RejectModerationRequest,
    SubmitForReviewRequest,
)

# Practice
from app.schemas.practice import (
    ActiveSessionResponse,
    AnswerBufferedResponse,
    ComparisonConfig,
    ItemHintSchema,
    SessionStartedResponse,
    SessionSummaryResponse,
    StartSessionRequest,
    SubmitAnswerRequest,
)

# Sets
from app.schemas.set import (
    SetCreateRequest,
    SetDetailResponse,
    SetLibraryEntryResponse,
    SetResponse,
    SetUpdateRequest,
)

# Stats
from app.schemas.stats import (
    DailyStatsQueryParams,
    DailyStatsResponse,
    HardestItemResponse,
    StatsRangeQueryParams,
    StatsRangeResponse,
    TotalStatsResponse,
)

# User
from app.schemas.user import (
    LanguageRefResponse,
    UserDetailResponse,
    UserPrivateResponse,
    UserPublicResponse,
    UserSettingsEmbedded,
    UserUpdateRequest,
)

# User settings
from app.schemas.user_settings import (
    UserSettingsPatchRequest,
    UserSettingsResponse,
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
