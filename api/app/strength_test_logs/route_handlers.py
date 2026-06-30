import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import current_user
from app.db import get_session
from app.errors import ErrorCode, api_error
from app.models import (
    BodyweightLog,
    Exercise,
    StrengthTestItem,
    StrengthTestLog,
    StrengthTestLogEntry,
    TrainingCategory,
    TrainingSubtype,
    User,
    UserRole,
)
from app.pagination import Page, PaginationParams
from app.strength_test_logs.schemas import (
    CreateStrengthTestLogRequest,
    LatestResult,
    LatestResultsResponse,
    StrengthTestLogEntryResponse,
    StrengthTestLogFormExercise,
    StrengthTestLogFormResponse,
    StrengthTestLogFormWeek,
    StrengthTestLogResponse,
    StrengthTestLogSummaryResponse,
    UpdateStrengthTestLogWeekRequest,
)
from app.week_progress import (
    incomplete_weeks_recommending,
    latest_used_week,
    recommended_week_id,
    weeks_recommending,
)

router = APIRouter(prefix="/strength-test-logs", tags=["strength-test-logs"])

# A strength-test log counts towards a week's test/strength requirement.
_CATEGORY = TrainingCategory.test
_SUBTYPE = TrainingSubtype.strength


async def _latest_bodyweight(session: AsyncSession, athlete_id: uuid.UUID) -> float | None:
    """The athlete's most recent body weight (kg), or None if they've logged none."""
    weight: float | None = await session.scalar(
        select(BodyweightLog.weight_kg)
        .where(BodyweightLog.athlete_id == athlete_id)
        .order_by(BodyweightLog.recorded_at.desc())
        .limit(1)
    )
    return weight


async def _test_exercises(session: AsyncSession) -> list[tuple[StrengthTestItem, Exercise]]:
    """The strength test's items in order, each with its exercise."""
    rows = await session.execute(
        select(StrengthTestItem, Exercise)
        .join(Exercise, StrengthTestItem.exercise_id == Exercise.id)
        .order_by(StrengthTestItem.position)
    )
    return [(item, exercise) for item, exercise in rows.all()]


async def _load_log(session: AsyncSession, log_id: uuid.UUID) -> StrengthTestLog | None:
    log: StrengthTestLog | None = await session.scalar(
        select(StrengthTestLog)
        .where(StrengthTestLog.id == log_id)
        .options(
            selectinload(StrengthTestLog.week),
            selectinload(StrengthTestLog.entries).selectinload(StrengthTestLogEntry.exercise),
        )
    )
    return log


def _serialize(log: StrengthTestLog) -> StrengthTestLogResponse:
    return StrengthTestLogResponse(
        id=log.id,
        performed_at=log.performed_at,
        bodyweight_kg=log.bodyweight_kg,
        week_id=log.week_id,
        week_name=log.week.name if log.week else None,
        entries=[
            StrengthTestLogEntryResponse(
                exercise_id=entry.exercise_id,
                exercise_name=entry.exercise.name,
                target_weight_kg=entry.target_weight_kg,
                actual_weight_kg=entry.actual_weight_kg,
            )
            for entry in log.entries
        ],
    )


@router.get("/form", response_model=StrengthTestLogFormResponse)
async def get_strength_test_log_form(
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> StrengthTestLogFormResponse:
    """What the athlete needs to take the test: their latest body weight, each
    exercise with its target load (body weight x multiplier), and the assignable
    weeks (those recommending test/strength and not yet full) + the recommended one."""
    bodyweight = await _latest_bodyweight(session, user.id)
    if bodyweight is None:
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            ErrorCode.no_bodyweight,
            "A body-weight register is required to take the test",
        )

    items = await _test_exercises(session)
    selectable = await incomplete_weeks_recommending(session, _CATEGORY, _SUBTYPE, user.id)
    latest = await latest_used_week(session, user.id)
    return StrengthTestLogFormResponse(
        bodyweight_kg=bodyweight,
        exercises=[
            StrengthTestLogFormExercise(
                exercise_id=exercise.id,
                exercise_name=exercise.name,
                weight_multiplier=item.weight_multiplier,
                target_weight_kg=round(bodyweight * item.weight_multiplier, 2),
            )
            for item, exercise in items
        ],
        weeks=[StrengthTestLogFormWeek(id=week.id, name=week.name) for week in selectable],
        recommended_week_id=recommended_week_id(latest, selectable),
    )


@router.post("", response_model=StrengthTestLogResponse, status_code=status.HTTP_201_CREATED)
async def create_strength_test_log(
    body: CreateStrengthTestLogRequest,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> StrengthTestLogResponse:
    """Record the current athlete taking the strength test: the actual load lifted per
    exercise (targets frozen from their latest body weight) and the optional week."""
    bodyweight = await _latest_bodyweight(session, user.id)
    if bodyweight is None:
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            ErrorCode.no_bodyweight,
            "A body-weight register is required to take the test",
        )

    items = await _test_exercises(session)
    if not items:
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            ErrorCode.empty_strength_test,
            "The strength test has no exercises yet",
        )

    if body.week_id is not None:
        valid = {week.id for week in await weeks_recommending(session, _CATEGORY, _SUBTYPE)}
        if body.week_id not in valid:
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.invalid_strength_test_log,
                "That week doesn't recommend a strength test",
            )

    # The actual weight submitted per exercise; every test exercise must be present.
    actual_by_exercise = {entry.exercise_id: entry.actual_weight_kg for entry in body.entries}
    log = StrengthTestLog(athlete_id=user.id, bodyweight_kg=bodyweight, week_id=body.week_id)
    for position, (item, exercise) in enumerate(items):
        actual = actual_by_exercise.get(exercise.id)
        if actual is None or actual <= 0:
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.invalid_strength_test_log,
                "Each exercise needs a positive weight",
            )
        log.entries.append(
            StrengthTestLogEntry(
                position=position,
                exercise_id=exercise.id,
                target_weight_kg=round(bodyweight * item.weight_multiplier, 2),
                actual_weight_kg=actual,
            )
        )

    session.add(log)
    await session.commit()

    reloaded = await _load_log(session, log.id)
    assert reloaded is not None
    return _serialize(reloaded)


@router.get("/latest-results", response_model=LatestResultsResponse)
async def latest_strength_test_results(
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LatestResultsResponse:
    """The current athlete's most recent lifted weight per exercise, across all their
    strength-test logs. Used to turn a training item's load % into absolute kg."""
    rows = await session.execute(
        select(
            StrengthTestLogEntry.exercise_id,
            StrengthTestLogEntry.actual_weight_kg,
            StrengthTestLog.performed_at,
        )
        .join(StrengthTestLog, StrengthTestLogEntry.log_id == StrengthTestLog.id)
        .where(StrengthTestLog.athlete_id == user.id)
        .order_by(StrengthTestLog.performed_at.desc())
    )
    # Rows are newest-first, so the first time we see an exercise is its latest result.
    latest: dict[uuid.UUID, float] = {}
    for exercise_id, weight, _performed_at in rows.all():
        latest.setdefault(exercise_id, weight)
    return LatestResultsResponse(
        results=[
            LatestResult(exercise_id=exercise_id, weight_kg=weight)
            for exercise_id, weight in latest.items()
        ]
    )


@router.get("", response_model=Page[StrengthTestLogSummaryResponse])
async def list_strength_test_logs(
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    params: Annotated[PaginationParams, Query()],
) -> Page[StrengthTestLogSummaryResponse]:
    """The current athlete's strength-test logs, most recent first."""
    total = await session.scalar(
        select(func.count())
        .select_from(StrengthTestLog)
        .where(StrengthTestLog.athlete_id == user.id)
    )
    rows = await session.scalars(
        select(StrengthTestLog)
        .where(StrengthTestLog.athlete_id == user.id)
        .order_by(StrengthTestLog.performed_at.desc())
        .offset(params.offset)
        .limit(params.page_size)
    )
    return Page(
        items=[StrengthTestLogSummaryResponse.model_validate(row) for row in rows.all()],
        total_count=total or 0,
    )


@router.get("/{log_id}", response_model=StrengthTestLogResponse)
async def get_strength_test_log(
    log_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> StrengthTestLogResponse:
    """A strength-test log's detail. The athlete can read their own; an admin can
    read any athlete's (to review tests from the user-detail page)."""
    log = await _load_log(session, log_id)
    owns_or_admin = log is not None and (log.athlete_id == user.id or user.role == UserRole.admin)
    if log is None or not owns_or_admin:
        raise api_error(
            status.HTTP_404_NOT_FOUND,
            ErrorCode.strength_test_log_not_found,
            "Strength test log not found",
        )
    return _serialize(log)


@router.patch("/{log_id}/week", response_model=StrengthTestLogResponse)
async def update_strength_test_log_week(
    log_id: uuid.UUID,
    body: UpdateStrengthTestLogWeekRequest,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> StrengthTestLogResponse:
    """Change (or clear) which calendar week this strength-test log counts towards."""
    log = await _load_log(session, log_id)
    if log is None or log.athlete_id != user.id:
        raise api_error(
            status.HTTP_404_NOT_FOUND,
            ErrorCode.strength_test_log_not_found,
            "Strength test log not found",
        )

    if body.week_id is not None:
        valid = {week.id for week in await weeks_recommending(session, _CATEGORY, _SUBTYPE)}
        if body.week_id not in valid:
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.invalid_strength_test_log,
                "That week doesn't recommend a strength test",
            )

    log.week_id = body.week_id
    await session.commit()

    reloaded = await _load_log(session, log_id)
    assert reloaded is not None
    return _serialize(reloaded)
