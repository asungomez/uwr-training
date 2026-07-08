import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import current_user
from app.db import get_session
from app.errors import ErrorCode, api_error
from app.lactic_acid_test_logs.schemas import (
    CreateLacticAcidTestLogRequest,
    CreateLacticAcidTestLogResponse,
    LacticAcidTestLogFormResponse,
    LacticAcidTestLogFormWeek,
    LacticAcidTestLogResponse,
    LacticAcidTestLogSummaryResponse,
)
from app.lactic_acid_test_warmup.route_handlers import _get_or_create_warmup_session
from app.models import (
    LacticAcidPersonalBestLog,
    LacticAcidTestResultLog,
    TrainingCategory,
    TrainingSubtype,
    User,
    UserRole,
)
from app.trainings.schemas import TrainingSessionDetailResponse
from app.week_progress import (
    incomplete_weeks_recommending,
    latest_used_week,
    recommended_week_id,
    weeks_recommending,
)

router = APIRouter(prefix="/lactic-acid-test-logs", tags=["lactic-acid-test-logs"])

# A lactic-acid-test log counts towards a week's test/lactic requirement.
_CATEGORY = TrainingCategory.test
_SUBTYPE = TrainingSubtype.lactic

# The two logs share one table shape; a `Log` is either. Keep them typed distinctly.
type LacticLog = LacticAcidPersonalBestLog | LacticAcidTestResultLog
type LogKind = Literal["personal-best", "test-result"]

# The number of most-recent points the history graphs plot.
GRAPH_POINTS = 10


async def _load_pb(session: AsyncSession, log_id: uuid.UUID) -> LacticAcidPersonalBestLog | None:
    log: LacticAcidPersonalBestLog | None = await session.scalar(
        select(LacticAcidPersonalBestLog)
        .where(LacticAcidPersonalBestLog.id == log_id)
        .options(selectinload(LacticAcidPersonalBestLog.week))
    )
    return log


async def _load_result(session: AsyncSession, log_id: uuid.UUID) -> LacticAcidTestResultLog | None:
    log: LacticAcidTestResultLog | None = await session.scalar(
        select(LacticAcidTestResultLog)
        .where(LacticAcidTestResultLog.id == log_id)
        .options(selectinload(LacticAcidTestResultLog.week))
    )
    return log


def _serialize(log: LacticLog, kind: LogKind) -> LacticAcidTestLogResponse:
    return LacticAcidTestLogResponse(
        id=log.id,
        kind=kind,
        performed_at=log.performed_at,
        seconds=log.seconds,
        week_id=log.week_id,
        week_name=log.week.name if log.week else None,
    )


@router.get("/form", response_model=LacticAcidTestLogFormResponse)
async def get_lactic_acid_test_log_form(
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LacticAcidTestLogFormResponse:
    """What the athlete needs to take the lactic-acid test: the warmup session
    (read-only) plus the assignable weeks (recommending test/lactic, not yet full)
    and the recommended one to pre-select."""
    warmup = await _get_or_create_warmup_session(session)
    selectable = await incomplete_weeks_recommending(session, _CATEGORY, _SUBTYPE, user.id)
    latest = await latest_used_week(session, user.id)
    return LacticAcidTestLogFormResponse(
        warmup=TrainingSessionDetailResponse.model_validate(warmup),
        weeks=[LacticAcidTestLogFormWeek(id=week.id, name=week.name) for week in selectable],
        recommended_week_id=recommended_week_id(latest, selectable),
    )


@router.post(
    "",
    response_model=CreateLacticAcidTestLogResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_lactic_acid_test_log(
    body: CreateLacticAcidTestLogRequest,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CreateLacticAcidTestLogResponse:
    """Record the lactic-acid test: the personal best, the test result, or both. At
    least one time must be present, and each present one is saved as its own log
    (both sharing the optional week)."""
    if body.personal_best is None and body.test_result is None:
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            ErrorCode.invalid_lactic_acid_test_log,
            "At least one of personal_best or test_result must be present",
        )
    for value in (body.personal_best, body.test_result):
        if value is not None and value <= 0:
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.invalid_lactic_acid_test_log,
                "The time must be greater than 0",
            )

    if body.week_id is not None:
        valid = {week.id for week in await weeks_recommending(session, _CATEGORY, _SUBTYPE)}
        if body.week_id not in valid:
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.invalid_lactic_acid_test_log,
                "That week doesn't recommend a lactic-acid test",
            )

    pb: LacticAcidPersonalBestLog | None = None
    result: LacticAcidTestResultLog | None = None
    if body.personal_best is not None:
        pb = LacticAcidPersonalBestLog(
            athlete_id=user.id, seconds=body.personal_best, week_id=body.week_id
        )
        session.add(pb)
    if body.test_result is not None:
        result = LacticAcidTestResultLog(
            athlete_id=user.id, seconds=body.test_result, week_id=body.week_id
        )
        session.add(result)
    await session.commit()

    response = CreateLacticAcidTestLogResponse()
    if pb is not None:
        reloaded_pb = await _load_pb(session, pb.id)
        assert reloaded_pb is not None
        response.personal_best = _serialize(reloaded_pb, "personal-best")
    if result is not None:
        reloaded_result = await _load_result(session, result.id)
        assert reloaded_result is not None
        response.test_result = _serialize(reloaded_result, "test-result")
    return response


@router.get("/personal-best/recent", response_model=list[LacticAcidTestLogSummaryResponse])
async def recent_personal_best_logs(
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[LacticAcidPersonalBestLog]:
    """The athlete's last few personal-best times for the history graph, oldest first
    so the chart reads left-to-right. Fixed-size."""
    rows = await session.scalars(
        select(LacticAcidPersonalBestLog)
        .where(LacticAcidPersonalBestLog.athlete_id == user.id)
        .order_by(LacticAcidPersonalBestLog.performed_at.desc())
        .limit(GRAPH_POINTS)
    )
    return list(reversed(rows.all()))


@router.get("/test-result/recent", response_model=list[LacticAcidTestLogSummaryResponse])
async def recent_test_result_logs(
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[LacticAcidTestResultLog]:
    """The athlete's last few test-result times for the history graph, oldest first so
    the chart reads left-to-right. Fixed-size."""
    rows = await session.scalars(
        select(LacticAcidTestResultLog)
        .where(LacticAcidTestResultLog.athlete_id == user.id)
        .order_by(LacticAcidTestResultLog.performed_at.desc())
        .limit(GRAPH_POINTS)
    )
    return list(reversed(rows.all()))


@router.get("/latest-personal-best", response_model=LacticAcidTestLogResponse | None)
async def get_latest_personal_best(
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LacticAcidTestLogResponse | None:
    """The athlete's most recent personal-best log, or null if they have none. Used to
    build the test-result interpretation table (which is relative to the personal
    best)."""
    log: LacticAcidPersonalBestLog | None = await session.scalar(
        select(LacticAcidPersonalBestLog)
        .where(LacticAcidPersonalBestLog.athlete_id == user.id)
        .order_by(LacticAcidPersonalBestLog.performed_at.desc())
        .options(selectinload(LacticAcidPersonalBestLog.week))
        .limit(1)
    )
    return _serialize(log, "personal-best") if log is not None else None


@router.get("/personal-best/{log_id}", response_model=LacticAcidTestLogResponse)
async def get_personal_best_log(
    log_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LacticAcidTestLogResponse:
    """A personal-best log's detail. The athlete can read their own; an admin can read
    any athlete's (to review tests from the user-detail page)."""
    log = await _load_pb(session, log_id)
    owns_or_admin = log is not None and (log.athlete_id == user.id or user.role == UserRole.admin)
    if log is None or not owns_or_admin:
        raise api_error(
            status.HTTP_404_NOT_FOUND,
            ErrorCode.lactic_acid_test_log_not_found,
            "Lactic-acid test log not found",
        )
    return _serialize(log, "personal-best")


@router.get("/test-result/{log_id}", response_model=LacticAcidTestLogResponse)
async def get_test_result_log(
    log_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LacticAcidTestLogResponse:
    """A test-result log's detail. Same access rules as the personal-best detail."""
    log = await _load_result(session, log_id)
    owns_or_admin = log is not None and (log.athlete_id == user.id or user.role == UserRole.admin)
    if log is None or not owns_or_admin:
        raise api_error(
            status.HTTP_404_NOT_FOUND,
            ErrorCode.lactic_acid_test_log_not_found,
            "Lactic-acid test log not found",
        )
    return _serialize(log, "test-result")
