import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import current_user
from app.cardio_logs.schemas import (
    CardioLogFormResponse,
    CardioLogFormWeek,
    CardioLogResponse,
    CardioLogSummaryResponse,
    CreateCardioLogRequest,
    UpdateCardioLogWeekRequest,
)
from app.db import get_session
from app.errors import ErrorCode, api_error
from app.models import (
    CardioSessionLog,
    CardioTraining,
    TrainingCategory,
    TrainingSubtype,
    User,
    UserRole,
)
from app.pagination import Page, PaginationParams
from app.week_progress import (
    incomplete_weeks_recommending,
    latest_used_week,
    recommended_week_id,
    weeks_recommending,
)

# Mounted under the cardio-trainings prefix so the log endpoints sit on a session.
router = APIRouter(prefix="/cardio-trainings", tags=["cardio-logs"])


def _cardio_type(training: CardioTraining) -> tuple[TrainingCategory, TrainingSubtype]:
    """A cardio training counts towards a week's cardio/<subtype> requirement."""
    return TrainingCategory.cardio, TrainingSubtype(training.subtype.value)


async def _load_log(session: AsyncSession, log_id: uuid.UUID) -> CardioSessionLog | None:
    log: CardioSessionLog | None = await session.scalar(
        select(CardioSessionLog)
        .where(CardioSessionLog.id == log_id)
        .options(selectinload(CardioSessionLog.week))
    )
    return log


def _serialize(log: CardioSessionLog) -> CardioLogResponse:
    return CardioLogResponse(
        id=log.id,
        cardio_training_id=log.cardio_training_id,
        performed_at=log.performed_at,
        exercise=log.exercise,
        note=log.note,
        week_id=log.week_id,
        week_name=log.week.name if log.week else None,
    )


@router.get("/{training_id}/log-form", response_model=CardioLogFormResponse)
async def get_cardio_log_form(
    training_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CardioLogFormResponse:
    """What the athlete needs to log this cardio session: the assignable weeks (those
    recommending its type and not yet full) plus the recommended one to pre-select."""
    training = await session.get(CardioTraining, training_id)
    if training is None:
        raise api_error(
            status.HTTP_404_NOT_FOUND,
            ErrorCode.cardio_training_not_found,
            "Cardio training not found",
        )

    category, subtype = _cardio_type(training)
    selectable = await incomplete_weeks_recommending(session, category, subtype, user.id)
    latest = await latest_used_week(session, user.id)
    return CardioLogFormResponse(
        cardio_training_id=training.id,
        title=training.title,
        weeks=[CardioLogFormWeek(id=week.id, name=week.name) for week in selectable],
        recommended_week_id=recommended_week_id(latest, selectable),
    )


@router.post(
    "/{training_id}/logs",
    response_model=CardioLogResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_cardio_log(
    training_id: uuid.UUID,
    body: CreateCardioLogRequest,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CardioLogResponse:
    """Record that the current athlete did this cardio session — the activity done,
    a note, and the optional week it counts towards."""
    training = await session.get(CardioTraining, training_id)
    if training is None:
        raise api_error(
            status.HTTP_404_NOT_FOUND,
            ErrorCode.cardio_training_not_found,
            "Cardio training not found",
        )

    if body.week_id is not None:
        category, subtype = _cardio_type(training)
        valid = {week.id for week in await weeks_recommending(session, category, subtype)}
        if body.week_id not in valid:
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.invalid_cardio_log,
                "That week doesn't recommend this type of training",
            )

    log = CardioSessionLog(
        cardio_training_id=training.id,
        athlete_id=user.id,
        exercise=(body.exercise.strip() if body.exercise else None) or None,
        note=(body.note.strip() if body.note else None) or None,
        week_id=body.week_id,
    )
    session.add(log)
    await session.commit()

    reloaded = await _load_log(session, log.id)
    assert reloaded is not None
    return _serialize(reloaded)


@router.get("/{training_id}/logs", response_model=Page[CardioLogSummaryResponse])
async def list_cardio_logs(
    training_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    params: Annotated[PaginationParams, Query()],
) -> Page[CardioLogSummaryResponse]:
    """The current athlete's own logs for this cardio session, most recent first."""
    filters = (
        CardioSessionLog.cardio_training_id == training_id,
        CardioSessionLog.athlete_id == user.id,
    )
    total = await session.scalar(select(func.count()).select_from(CardioSessionLog).where(*filters))
    rows = await session.scalars(
        select(CardioSessionLog)
        .where(*filters)
        .order_by(CardioSessionLog.performed_at.desc())
        .offset(params.offset)
        .limit(params.page_size)
    )
    return Page(
        items=[CardioLogSummaryResponse.model_validate(row) for row in rows.all()],
        total_count=total or 0,
    )


@router.get("/{training_id}/logs/{log_id}", response_model=CardioLogResponse)
async def get_cardio_log(
    training_id: uuid.UUID,
    log_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CardioLogResponse:
    """A cardio log's detail. The athlete can read their own; an admin can read any
    athlete's (to review training from the user-detail page)."""
    log = await _load_log(session, log_id)
    owns_or_admin = log is not None and (log.athlete_id == user.id or user.role == UserRole.admin)
    if log is None or log.cardio_training_id != training_id or not owns_or_admin:
        raise api_error(
            status.HTTP_404_NOT_FOUND, ErrorCode.cardio_log_not_found, "Cardio log not found"
        )
    return _serialize(log)


@router.patch("/{training_id}/logs/{log_id}/week", response_model=CardioLogResponse)
async def update_cardio_log_week(
    training_id: uuid.UUID,
    log_id: uuid.UUID,
    body: UpdateCardioLogWeekRequest,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CardioLogResponse:
    """Change (or clear) which calendar week this cardio log counts towards."""
    log = await _load_log(session, log_id)
    if log is None or log.cardio_training_id != training_id or log.athlete_id != user.id:
        raise api_error(
            status.HTTP_404_NOT_FOUND, ErrorCode.cardio_log_not_found, "Cardio log not found"
        )

    if body.week_id is not None:
        training = await session.get(CardioTraining, training_id)
        assert training is not None
        category, subtype = _cardio_type(training)
        valid = {week.id for week in await weeks_recommending(session, category, subtype)}
        if body.week_id not in valid:
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.invalid_cardio_log,
                "That week doesn't recommend this type of training",
            )

    log.week_id = body.week_id
    await session.commit()

    reloaded = await _load_log(session, log_id)
    assert reloaded is not None
    return _serialize(reloaded)
