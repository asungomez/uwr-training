import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
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
)
from app.session_logs.schemas import (
    CreateSessionLogRequest,
    LogEntryResponse,
    LogFormAlternative,
    LogFormExercise,
    LogFormParameter,
    LogFormResponse,
    LogParameterValueResponse,
    SessionLogResponse,
    SessionLogSummaryResponse,
)

# Mounted under the trainings prefix so the log endpoints sit on a session.
router = APIRouter(prefix="/trainings", tags=["session-logs"])


async def _load_session_exercises(
    session: AsyncSession, training_id: uuid.UUID
) -> TrainingSession | None:
    """Fetch a session with its series items' exercises, and each exercise's
    related (alternatives) + parameters loaded — for the log form."""
    training: TrainingSession | None = await session.scalar(
        select(TrainingSession)
        .where(TrainingSession.id == training_id)
        .options(
            selectinload(TrainingSession.blocks)
            .selectinload(TrainingBlock.sub_blocks)
            .selectinload(TrainingSubBlock.items)
            .selectinload(TrainingItem.exercise)
            .selectinload(Exercise.related)
            .selectinload(ExerciseRelation.related_exercise),
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
            selectinload(SessionLog.entries).selectinload(SessionLogEntry.planned_exercise),
            selectinload(SessionLog.entries).selectinload(SessionLogEntry.performed_exercise),
            selectinload(SessionLog.entries)
            .selectinload(SessionLogEntry.parameter_values)
            .selectinload(SessionLogParameterValue.parameter),
        )
    )
    return log


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
        entries=entries,
    )


@router.get("/{training_id}/log-form", response_model=LogFormResponse)
async def get_log_form(
    training_id: uuid.UUID,
    _user: Annotated[User, Depends(current_user)],
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
    return LogFormResponse(training_id=training.id, title=training.title, exercises=exercises)


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

    note = body.note.strip() if body.note else None
    log = SessionLog(training_session_id=training.id, athlete_id=user.id, note=note or None)
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

        params_by_id = {param.id: param for param in planned.parameters}
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


@router.get("/{training_id}/logs", response_model=list[SessionLogSummaryResponse])
async def list_session_logs(
    training_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[SessionLog]:
    """The current athlete's own logs for this session, most recent first."""
    rows = await session.scalars(
        select(SessionLog)
        .where(
            SessionLog.training_session_id == training_id,
            SessionLog.athlete_id == user.id,
        )
        .order_by(SessionLog.performed_at.desc())
    )
    return list(rows.all())


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
