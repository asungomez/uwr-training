import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import current_user
from app.db import get_session
from app.errors import ErrorCode, api_error
from app.models import SpeedTestLog, TrainingCategory, TrainingSubtype, User
from app.pagination import Page, PaginationParams
from app.speed_test_logs.schemas import (
    CreateSpeedTestLogRequest,
    SpeedTestLogFormResponse,
    SpeedTestLogFormWeek,
    SpeedTestLogResponse,
    SpeedTestLogSummaryResponse,
    UpdateSpeedTestLogWeekRequest,
)
from app.speed_test_warmup.route_handlers import _get_or_create_warmup_session
from app.trainings.schemas import TrainingSessionDetailResponse
from app.week_progress import (
    incomplete_weeks_recommending,
    latest_used_week,
    recommended_week_id,
    weeks_recommending,
)

router = APIRouter(prefix="/speed-test-logs", tags=["speed-test-logs"])

# A speed-test log counts towards a week's test/speed requirement.
_CATEGORY = TrainingCategory.test
_SUBTYPE = TrainingSubtype.speed


async def _load_log(session: AsyncSession, log_id: uuid.UUID) -> SpeedTestLog | None:
    log: SpeedTestLog | None = await session.scalar(
        select(SpeedTestLog)
        .where(SpeedTestLog.id == log_id)
        .options(selectinload(SpeedTestLog.week))
    )
    return log


def _serialize(log: SpeedTestLog) -> SpeedTestLogResponse:
    return SpeedTestLogResponse(
        id=log.id,
        performed_at=log.performed_at,
        seconds=log.seconds,
        week_id=log.week_id,
        week_name=log.week.name if log.week else None,
    )


@router.get("/form", response_model=SpeedTestLogFormResponse)
async def get_speed_test_log_form(
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SpeedTestLogFormResponse:
    """What the athlete needs to take the speed test: the warmup session (read-only)
    plus the assignable weeks (recommending test/speed, not yet full) + recommended."""
    warmup = await _get_or_create_warmup_session(session)
    selectable = await incomplete_weeks_recommending(session, _CATEGORY, _SUBTYPE, user.id)
    latest = await latest_used_week(session, user.id)
    return SpeedTestLogFormResponse(
        warmup=TrainingSessionDetailResponse.model_validate(warmup),
        weeks=[SpeedTestLogFormWeek(id=week.id, name=week.name) for week in selectable],
        recommended_week_id=recommended_week_id(latest, selectable),
    )


@router.post("", response_model=SpeedTestLogResponse, status_code=status.HTTP_201_CREATED)
async def create_speed_test_log(
    body: CreateSpeedTestLogRequest,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SpeedTestLogResponse:
    """Record the current athlete taking the speed test: the 25 m time (seconds) and
    the optional week it counts towards."""
    if body.seconds <= 0:
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            ErrorCode.invalid_speed_test_log,
            "The time must be greater than 0",
        )

    if body.week_id is not None:
        valid = {week.id for week in await weeks_recommending(session, _CATEGORY, _SUBTYPE)}
        if body.week_id not in valid:
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.invalid_speed_test_log,
                "That week doesn't recommend a speed test",
            )

    log = SpeedTestLog(athlete_id=user.id, seconds=body.seconds, week_id=body.week_id)
    session.add(log)
    await session.commit()

    reloaded = await _load_log(session, log.id)
    assert reloaded is not None
    return _serialize(reloaded)


@router.get("", response_model=Page[SpeedTestLogSummaryResponse])
async def list_speed_test_logs(
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    params: Annotated[PaginationParams, Query()],
) -> Page[SpeedTestLogSummaryResponse]:
    """The current athlete's speed-test logs, most recent first."""
    total = await session.scalar(
        select(func.count()).select_from(SpeedTestLog).where(SpeedTestLog.athlete_id == user.id)
    )
    rows = await session.scalars(
        select(SpeedTestLog)
        .where(SpeedTestLog.athlete_id == user.id)
        .order_by(SpeedTestLog.performed_at.desc())
        .offset(params.offset)
        .limit(params.page_size)
    )
    return Page(
        items=[SpeedTestLogSummaryResponse.model_validate(row) for row in rows.all()],
        total_count=total or 0,
    )


@router.get("/{log_id}", response_model=SpeedTestLogResponse)
async def get_speed_test_log(
    log_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SpeedTestLogResponse:
    """One of the current athlete's speed-test logs."""
    log = await _load_log(session, log_id)
    if log is None or log.athlete_id != user.id:
        raise api_error(
            status.HTTP_404_NOT_FOUND,
            ErrorCode.speed_test_log_not_found,
            "Speed test log not found",
        )
    return _serialize(log)


@router.patch("/{log_id}/week", response_model=SpeedTestLogResponse)
async def update_speed_test_log_week(
    log_id: uuid.UUID,
    body: UpdateSpeedTestLogWeekRequest,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SpeedTestLogResponse:
    """Change (or clear) which calendar week this speed-test log counts towards."""
    log = await _load_log(session, log_id)
    if log is None or log.athlete_id != user.id:
        raise api_error(
            status.HTTP_404_NOT_FOUND,
            ErrorCode.speed_test_log_not_found,
            "Speed test log not found",
        )

    if body.week_id is not None:
        valid = {week.id for week in await weeks_recommending(session, _CATEGORY, _SUBTYPE)}
        if body.week_id not in valid:
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.invalid_speed_test_log,
                "That week doesn't recommend a speed test",
            )

    log.week_id = body.week_id
    await session.commit()

    reloaded = await _load_log(session, log_id)
    assert reloaded is not None
    return _serialize(reloaded)
