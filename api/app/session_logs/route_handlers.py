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
    Exercise,
    ExerciseRelation,
    SessionLog,
    SessionLogAction,
    SessionLogEntry,
    SessionLogParameterValue,
    TrainingBlock,
    TrainingItem,
    TrainingItemKind,
    TrainingSession,
    TrainingSubBlock,
    User,
    Week,
    WeekRequirement,
)
from app.pagination import Page, PaginationParams
from app.session_logs.schemas import (
    CreateSessionLogRequest,
    LogEntryResponse,
    LogFormAlternative,
    LogFormExercise,
    LogFormParameter,
    LogFormResponse,
    LogFormWeek,
    LogParameterValueResponse,
    SessionLogResponse,
    SessionLogSummaryResponse,
    UpdateSessionLogWeekRequest,
)

# Mounted under the trainings prefix so the log endpoints sit on a session.
router = APIRouter(prefix="/trainings", tags=["session-logs"])


async def _load_session_exercises(
    session: AsyncSession, training_id: uuid.UUID
) -> TrainingSession | None:
    """Fetch a session with its series items' exercises, each exercise's parameters
    and its alternatives (with the alternative's own parameters) loaded — for the
    log form, where switching to an alternative shows the alternative's parameters."""
    training: TrainingSession | None = await session.scalar(
        select(TrainingSession)
        .where(TrainingSession.id == training_id)
        .options(
            selectinload(TrainingSession.blocks)
            .selectinload(TrainingBlock.sub_blocks)
            .selectinload(TrainingSubBlock.items)
            .selectinload(TrainingItem.exercise)
            .selectinload(Exercise.related)
            .selectinload(ExerciseRelation.related_exercise)
            .selectinload(Exercise.parameters),
            selectinload(TrainingSession.blocks)
            .selectinload(TrainingBlock.sub_blocks)
            .selectinload(TrainingSubBlock.items)
            .selectinload(TrainingItem.exercise)
            .selectinload(Exercise.parameters),
        )
    )
    return training


def _ordered_series_exercises(training: TrainingSession) -> list[Exercise]:
    """Every series item's exercise, in session order, de-duplicated by exercise
    (the same exercise appearing twice yields one form entry)."""
    seen: set[uuid.UUID] = set()
    exercises: list[Exercise] = []
    for block in training.blocks:
        for sub in block.sub_blocks:
            for item in sub.items:
                if item.kind != TrainingItemKind.series or item.exercise is None:
                    continue
                if item.exercise.id in seen:
                    continue
                seen.add(item.exercise.id)
                exercises.append(item.exercise)
    return exercises


async def _load_full_log(session: AsyncSession, log_id: uuid.UUID) -> SessionLog | None:
    """Fetch a log with its entries' planned/performed exercises and parameter
    values + parameters loaded — everything `_serialize_log` needs."""
    log: SessionLog | None = await session.scalar(
        select(SessionLog)
        .where(SessionLog.id == log_id)
        .options(
            selectinload(SessionLog.week),
            selectinload(SessionLog.entries).selectinload(SessionLogEntry.planned_exercise),
            selectinload(SessionLog.entries).selectinload(SessionLogEntry.performed_exercise),
            selectinload(SessionLog.entries)
            .selectinload(SessionLogEntry.parameter_values)
            .selectinload(SessionLogParameterValue.parameter),
        )
    )
    return log


async def _weeks_recommending(session: AsyncSession, training: TrainingSession) -> list[Week]:
    """Weeks whose requirements include this training's category+subtype, in order.
    These are the weeks a log of this session can be assigned to."""
    rows = await session.scalars(
        select(Week)
        .join(WeekRequirement, WeekRequirement.week_id == Week.id)
        .where(
            WeekRequirement.category == training.category,
            WeekRequirement.subtype == training.subtype,
        )
        .order_by(Week.position)
        .distinct()
    )
    return list(rows.all())


async def _incomplete_weeks_recommending(
    session: AsyncSession, training: TrainingSession, athlete_id: uuid.UUID
) -> list[Week]:
    """The recommending weeks whose requirement for this training's type the athlete
    hasn't fulfilled yet — i.e. fewer matching logs linked than the week recommends.
    These are the weeks worth offering in the log form's dropdown."""
    weeks = await _weeks_recommending(session, training)
    if not weeks:
        return weeks

    week_ids = [week.id for week in weeks]

    # The recommended count per week for this exact type.
    required: dict[uuid.UUID, int] = {}
    for week_id, count in (
        await session.execute(
            select(WeekRequirement.week_id, WeekRequirement.count).where(
                WeekRequirement.week_id.in_(week_ids),
                WeekRequirement.category == training.category,
                WeekRequirement.subtype == training.subtype,
            )
        )
    ).all():
        required[week_id] = count

    # How many of the athlete's logs of this type are already linked to each week.
    done: dict[uuid.UUID, int] = {}
    for week_id, count in (
        await session.execute(
            select(SessionLog.week_id, func.count())
            .join(TrainingSession, SessionLog.training_session_id == TrainingSession.id)
            .where(
                SessionLog.athlete_id == athlete_id,
                SessionLog.week_id.in_(week_ids),
                TrainingSession.category == training.category,
                TrainingSession.subtype == training.subtype,
            )
            .group_by(SessionLog.week_id)
        )
    ).all():
        done[week_id] = count

    return [week for week in weeks if done.get(week.id, 0) < required.get(week.id, 0)]


async def _latest_used_week_id(session: AsyncSession, athlete_id: uuid.UUID) -> uuid.UUID | None:
    """The week the athlete most recently linked any logged session to (of any type),
    or None if they've never linked a log to a week."""
    return await session.scalar(
        select(SessionLog.week_id)
        .where(SessionLog.athlete_id == athlete_id, SessionLog.week_id.is_not(None))
        .order_by(SessionLog.performed_at.desc())
        .limit(1)
    )


def _serialize_log(log: SessionLog) -> SessionLogResponse:
    """Build the log response from a fully-loaded SessionLog (entries with their
    planned/performed exercises and parameter values + parameters)."""
    entries = []
    for entry in log.entries:
        performed = entry.performed_exercise
        entries.append(
            LogEntryResponse(
                id=entry.id,
                action=entry.action,
                planned_exercise_id=entry.planned_exercise_id,
                planned_exercise_name=entry.planned_exercise.name,
                performed_exercise_id=entry.performed_exercise_id,
                performed_exercise_name=performed.name if performed else None,
                is_alternative=(
                    performed is not None and performed.id != entry.planned_exercise_id
                ),
                parameter_values=[
                    LogParameterValueResponse(
                        id=value.id,
                        parameter_id=value.parameter_id,
                        name=value.parameter.name,
                        value=value.value,
                    )
                    for value in entry.parameter_values
                ],
            )
        )
    return SessionLogResponse(
        id=log.id,
        training_session_id=log.training_session_id,
        performed_at=log.performed_at,
        note=log.note,
        week_id=log.week_id,
        week_name=log.week.name if log.week else None,
        entries=entries,
    )


@router.get("/{training_id}/log-form", response_model=LogFormResponse)
async def get_log_form(
    training_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LogFormResponse:
    """The data an athlete needs to log a session: each exercise with its
    alternatives (to pick a substitution) and parameters (to record values)."""
    training = await _load_session_exercises(session, training_id)
    if training is None:
        raise api_error(
            status.HTTP_404_NOT_FOUND, ErrorCode.training_not_found, "Training not found"
        )

    exercises = [
        LogFormExercise(
            exercise_id=exercise.id,
            name=exercise.name,
            alternatives=[
                LogFormAlternative(
                    exercise_id=relation.related_exercise.id,
                    name=relation.related_exercise.name,
                    parameters=[
                        LogFormParameter(parameter_id=param.id, name=param.name)
                        for param in relation.related_exercise.parameters
                    ],
                )
                for relation in exercise.related
            ],
            parameters=[
                LogFormParameter(parameter_id=param.id, name=param.name)
                for param in exercise.parameters
            ],
        )
        for exercise in _ordered_series_exercises(training)
    ]
    # Only offer weeks whose requirement for this type the athlete hasn't already
    # filled — a full week isn't worth picking.
    selectable = await _incomplete_weeks_recommending(session, training, user.id)
    weeks = [LogFormWeek(id=week.id, name=week.name) for week in selectable]

    # Pre-select the week the athlete is currently working on — the latest one they
    # logged anything to — but only if it can still take this kind of training.
    latest = await _latest_used_week_id(session, user.id)
    selectable_ids = {week.id for week in selectable}
    recommended_week_id = latest if latest in selectable_ids else None

    return LogFormResponse(
        training_id=training.id,
        title=training.title,
        exercises=exercises,
        weeks=weeks,
        recommended_week_id=recommended_week_id,
    )


@router.post(
    "/{training_id}/logs",
    response_model=SessionLogResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_session_log(
    training_id: uuid.UUID,
    body: CreateSessionLogRequest,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SessionLogResponse:
    """Record that the current athlete went through this session: for each exercise,
    whether it was done or skipped, which exercise was actually performed (standard
    or an alternative), and the parameter values entered. Plus an optional note."""
    training = await _load_session_exercises(session, training_id)
    if training is None:
        raise api_error(
            status.HTTP_404_NOT_FOUND, ErrorCode.training_not_found, "Training not found"
        )

    # Index the session's exercises (with their valid alternatives + parameters) so we
    # can validate the submission without trusting the client.
    by_id = {exercise.id: exercise for exercise in _ordered_series_exercises(training)}

    # A chosen week must be one that recommends this training's type.
    if body.week_id is not None:
        valid_week_ids = {week.id for week in await _weeks_recommending(session, training)}
        if body.week_id not in valid_week_ids:
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.invalid_session_log,
                "That week doesn't recommend this type of training",
            )

    note = body.note.strip() if body.note else None
    log = SessionLog(
        training_session_id=training.id,
        athlete_id=user.id,
        note=note or None,
        week_id=body.week_id,
    )
    for position, entry in enumerate(body.entries):
        planned = by_id.get(entry.planned_exercise_id)
        if planned is None:
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.invalid_session_log,
                "Logged an exercise that isn't part of this session",
            )

        if entry.action == "skipped":
            # A skipped exercise carries no performed exercise or parameter values.
            log.entries.append(
                SessionLogEntry(
                    position=position,
                    action=SessionLogAction.skipped,
                    planned_exercise_id=planned.id,
                )
            )
            continue

        # Done: the performed exercise is the planned one or one of its alternatives.
        alternatives = {
            relation.related_exercise.id: relation.related_exercise for relation in planned.related
        }
        if entry.performed_exercise_id == planned.id:
            performed = planned
        elif entry.performed_exercise_id in alternatives:
            performed = alternatives[entry.performed_exercise_id]
        else:
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.invalid_session_log,
                "Performed exercise is not a valid option for this item",
            )

        # Parameters belong to the exercise actually performed (the alternative,
        # when swapped) — not the prescribed one.
        params_by_id = {param.id: param for param in performed.parameters}
        values = []
        for value_position, value in enumerate(entry.parameter_values):
            if value.parameter_id not in params_by_id:
                raise api_error(
                    status.HTTP_400_BAD_REQUEST,
                    ErrorCode.invalid_session_log,
                    "Recorded a parameter that doesn't belong to this exercise",
                )
            text = value.value.strip()
            if not text:
                continue  # skip blank values — the parameter just wasn't recorded
            values.append(
                SessionLogParameterValue(
                    position=value_position, parameter_id=value.parameter_id, value=text
                )
            )

        log.entries.append(
            SessionLogEntry(
                position=position,
                action=SessionLogAction.done,
                planned_exercise_id=planned.id,
                performed_exercise_id=performed.id,
                parameter_values=values,
            )
        )

    session.add(log)
    await session.commit()

    reloaded = await _load_full_log(session, log.id)
    assert reloaded is not None
    return _serialize_log(reloaded)


@router.get("/{training_id}/logs", response_model=Page[SessionLogSummaryResponse])
async def list_session_logs(
    training_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    params: Annotated[PaginationParams, Query()],
) -> Page[SessionLogSummaryResponse]:
    """The current athlete's own logs for this session, most recent first, paged."""
    filters = (
        SessionLog.training_session_id == training_id,
        SessionLog.athlete_id == user.id,
    )
    total = await session.scalar(select(func.count()).select_from(SessionLog).where(*filters))
    rows = await session.scalars(
        select(SessionLog)
        .where(*filters)
        .order_by(SessionLog.performed_at.desc())
        .offset(params.offset)
        .limit(params.page_size)
    )
    return Page(
        items=[SessionLogSummaryResponse.model_validate(row) for row in rows.all()],
        total_count=total or 0,
    )


@router.get("/{training_id}/logs/{log_id}", response_model=SessionLogResponse)
async def get_session_log(
    training_id: uuid.UUID,
    log_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SessionLogResponse:
    """One of the current athlete's logs for this session, with full detail."""
    log = await _load_full_log(session, log_id)
    if log is None or log.training_session_id != training_id or log.athlete_id != user.id:
        raise api_error(
            status.HTTP_404_NOT_FOUND, ErrorCode.session_log_not_found, "Session log not found"
        )
    return _serialize_log(log)


@router.patch("/{training_id}/logs/{log_id}/week", response_model=SessionLogResponse)
async def update_session_log_week(
    training_id: uuid.UUID,
    log_id: uuid.UUID,
    body: UpdateSessionLogWeekRequest,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SessionLogResponse:
    """Change (or clear) which calendar week this log counts towards. The week, if
    given, must recommend this training's type."""
    log = await _load_full_log(session, log_id)
    if log is None or log.training_session_id != training_id or log.athlete_id != user.id:
        raise api_error(
            status.HTTP_404_NOT_FOUND, ErrorCode.session_log_not_found, "Session log not found"
        )

    if body.week_id is not None:
        training = await session.get(TrainingSession, training_id)
        assert training is not None  # the log's session exists (it references it)
        valid_week_ids = {week.id for week in await _weeks_recommending(session, training)}
        if body.week_id not in valid_week_ids:
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.invalid_session_log,
                "That week doesn't recommend this type of training",
            )

    log.week_id = body.week_id
    await session.commit()

    reloaded = await _load_full_log(session, log_id)
    assert reloaded is not None
    return _serialize_log(reloaded)
