"""
Practice routes — HTTP layer only.

Routes → Services → Repositories → Models

No business logic. No SM-2. No Redis/DB access.

Study direction:
  User sees:   prompt (translation.term_trans)
  User types:  answer (item.term)

Buffered architecture:
  POST /sessions              → 201 Created (full batch + comparison_config)
  POST /sessions/{id}/answers → 202 Accepted (fire-and-forget; SM-2 deferred)
  POST /sessions/{id}/finalise  → 200 OK (batch SM-2 + DB commit)
  POST /sessions/{id}/abandon   → 200 OK (same flush path, ABANDONED status)
"""

from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import PracticeServiceDep
from app.core.exceptions import (
    BusinessRuleViolationError,
    NotAuthorizedToStudyError,
    ResourceNotFoundError,
)
from app.schemas.practice import (
    ActiveSessionResponse,
    AnswerBufferedResponse,
    ComparisonConfig,
    SessionStartedResponse,
    SessionSummaryResponse,
    StartSessionRequest,
    SubmitAnswerRequest,
)
from app.services.practice_service import (
    SubmitAnswerRequest as ServiceSubmitRequest,
)

router = APIRouter(prefix="/practice", tags=["practice"])


# ── Start session ─────────────────────────────────────────────────────────────


@router.post(
    "/sessions",
    response_model=SessionStartedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new practice session — returns the full item batch upfront",
)
async def start_session(
    body: StartSessionRequest,
    svc: PracticeServiceDep,
) -> SessionStartedResponse:
    try:
        return await svc.start_session(body.set_id)
    except ResourceNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))
    except NotAuthorizedToStudyError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc))
    except BusinessRuleViolationError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc))


# ── Active session recovery ───────────────────────────────────────────────────


@router.get(
    "/sessions/active",
    response_model=ActiveSessionResponse,
    summary="Get current in-progress session (for app-start recovery)",
)
async def get_active_session(svc: PracticeServiceDep) -> ActiveSessionResponse:
    state = await svc.get_active_session()
    if state is None:
        return ActiveSessionResponse(has_active_session=False)

    return ActiveSessionResponse(
        has_active_session=True,
        session_id=state.session_id,
        set_id=state.set_id,
        remaining_count=state.remaining_count,
    )


# ── Submit answer (fire-and-forget) ──────────────────────────────────────────


@router.post(
    "/sessions/{session_id}/answers",
    response_model=AnswerBufferedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Buffer one answer — SM-2 deferred to finalise",
)
async def submit_answer(
    session_id: int,
    body: SubmitAnswerRequest,
    svc: PracticeServiceDep,
) -> AnswerBufferedResponse:
    req = ServiceSubmitRequest(
        item_id=body.item_id,
        user_answer=body.user_answer,
        response_time_ms=body.response_time_ms,
        confidence_override=body.confidence_override,
        answer_id=body.answer_id,
    )

    try:
        is_correct, similarity, _, updated_state = await svc.submit_answer(session_id, req)
    except ResourceNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    return AnswerBufferedResponse(
        buffered=True,
        remaining_count=updated_state.remaining_count,
        is_batch_complete=updated_state.is_complete,
        is_correct=is_correct,
        similarity=round(similarity, 4),
    )


# ── Finalise ──────────────────────────────────────────────────────────────────


@router.post(
    "/sessions/{session_id}/finalise",
    response_model=SessionSummaryResponse,
    summary="Finalise session — batch SM-2 + DB commit",
)
async def finalise_session(
    session_id: int,
    svc: PracticeServiceDep,
) -> SessionSummaryResponse:
    try:
        summary = await svc.finalize_session(session_id)
    except ResourceNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))
    except NotAuthorizedToStudyError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc))
    except BusinessRuleViolationError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc))

    return SessionSummaryResponse(**summary)


# ── Abandon ───────────────────────────────────────────────────────────────────


@router.post(
    "/sessions/{session_id}/abandon",
    response_model=SessionSummaryResponse,
    summary="Abandon session — saves partial progress, marks ABANDONED",
)
async def abandon_session(
    session_id: int,
    svc: PracticeServiceDep,
) -> SessionSummaryResponse:
    try:
        summary = await svc.abandon_session(session_id)
    except ResourceNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))
    except NotAuthorizedToStudyError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc))
    except BusinessRuleViolationError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc))

    return SessionSummaryResponse(**summary)


@router.get(
    "/sessions/{session_id}/config",
    response_model=ComparisonConfig,
    summary="Re-read UserSettings and refresh session comparison config",
)
async def refresh_session_config(
    session_id: int,
    svc: PracticeServiceDep,
) -> ComparisonConfig:
    try:
        return await svc.refresh_comparison_config(session_id)
    except ResourceNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))
    except NotAuthorizedToStudyError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc))


# ── Summary ───────────────────────────────────────────────────────────────────


@router.get(
    "/sessions/{session_id}/summary",
    response_model=SessionSummaryResponse,
    summary="Read-only session summary (safe before and after finalisation)",
)
async def get_session_summary(
    session_id: int,
    svc: PracticeServiceDep,
) -> SessionSummaryResponse:
    try:
        summary = await svc.get_session_summary(session_id)
    except ResourceNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))
    except NotAuthorizedToStudyError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc))

    return SessionSummaryResponse(**summary)
