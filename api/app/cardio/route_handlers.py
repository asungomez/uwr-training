import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import current_user, require_admin
from app.cardio.schemas import (
    CardioItemInput,
    CardioListParams,
    CardioTrainingDetailResponse,
    CardioTrainingResponse,
    CreateCardioTrainingRequest,
    UpdateCardioPositionRequest,
    UpdateCardioTrainingRequest,
)
from app.db import get_session
from app.errors import ErrorCode, api_error
from app.models import (
    CardioInterval,
    CardioIntervalKind,
    CardioItem,
    CardioItemKind,
    CardioSubtype,
    CardioTraining,
    User,
)
from app.pagination import Page

router = APIRouter(prefix="/cardio-trainings", tags=["cardio"])


def _build_items(items: list[CardioItemInput]) -> list[CardioItem]:
    """Build ordered CardioItem rows from the submitted list — notes (free text)
    and blocks (a round of intervals repeated `repeats` times). Rejects a block
    with no intervals."""
    rows: list[CardioItem] = []
    for position, item in enumerate(items):
        if item.kind == "block":
            if not item.intervals:
                raise api_error(
                    status.HTTP_400_BAD_REQUEST,
                    ErrorCode.invalid_cardio_block,
                    "A block needs at least one interval",
                )
            intervals = [
                CardioInterval(
                    kind=CardioIntervalKind(interval.kind),
                    position=index,
                    duration_seconds=interval.duration_seconds,
                    intensity_pct=(interval.intensity_pct if interval.kind == "effort" else None),
                )
                for index, interval in enumerate(item.intervals)
            ]
            rows.append(
                CardioItem(
                    kind=CardioItemKind.block,
                    position=position,
                    repeats=max(1, item.repeats),
                    rest_seconds=item.rest_seconds,
                    intervals=intervals,
                )
            )
        else:
            text = item.text.strip() if item.text else None
            rows.append(CardioItem(kind=CardioItemKind.note, position=position, text=text or None))
    return rows


async def _next_position(session: AsyncSession, subtype: CardioSubtype) -> int:
    """The next free position at the end of a subtype scope."""
    max_position = await session.scalar(
        select(func.max(CardioTraining.position)).where(CardioTraining.subtype == subtype)
    )
    return 0 if max_position is None else max_position + 1


async def _load_with_items(session: AsyncSession, training_id: uuid.UUID) -> CardioTraining | None:
    """Fetch a cardio training with its items and their intervals (ordered) loaded."""
    training: CardioTraining | None = await session.scalar(
        select(CardioTraining)
        .where(CardioTraining.id == training_id)
        .options(selectinload(CardioTraining.items).selectinload(CardioItem.intervals))
    )
    return training


@router.get("")
async def list_cardio_trainings(
    _user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    params: Annotated[CardioListParams, Query()],
) -> Page[CardioTrainingResponse]:
    """All cardio trainings, filterable by title search and subtype. Visible to
    any authenticated user."""
    filters: list[ColumnElement[bool]] = []
    if params.search:
        filters.append(CardioTraining.title.ilike(f"%{params.search.strip()}%"))
    if params.subtype is not None:
        filters.append(CardioTraining.subtype == params.subtype)

    total = await session.scalar(select(func.count()).select_from(CardioTraining).where(*filters))
    rows = await session.scalars(
        select(CardioTraining)
        .where(*filters)
        .order_by(CardioTraining.position)
        .offset(params.offset)
        .limit(params.page_size)
    )
    return Page(
        items=[CardioTrainingResponse.model_validate(row) for row in rows.all()],
        total_count=total or 0,
    )


@router.get("/{training_id}", response_model=CardioTrainingDetailResponse)
async def get_cardio_training(
    training_id: uuid.UUID,
    _user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CardioTraining:
    """A single cardio training (with its items) by id. Visible to any user."""
    training = await _load_with_items(session, training_id)
    if training is None:
        raise api_error(
            status.HTTP_404_NOT_FOUND,
            ErrorCode.cardio_training_not_found,
            "Cardio training not found",
        )
    return training


@router.post("", response_model=CardioTrainingDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_cardio_training(
    body: CreateCardioTrainingRequest,
    _admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CardioTraining:
    title = body.title.strip() if body.title else None
    training = CardioTraining(
        subtype=body.subtype,
        position=await _next_position(session, body.subtype),
        title=title or None,
    )
    training.items = _build_items(body.items)
    session.add(training)
    await session.commit()

    reloaded = await _load_with_items(session, training.id)
    assert reloaded is not None
    return reloaded


@router.put("/{training_id}", response_model=CardioTrainingDetailResponse)
async def update_cardio_training(
    training_id: uuid.UUID,
    body: UpdateCardioTrainingRequest,
    _admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CardioTraining:
    training = await _load_with_items(session, training_id)
    if training is None:
        raise api_error(
            status.HTTP_404_NOT_FOUND,
            ErrorCode.cardio_training_not_found,
            "Cardio training not found",
        )

    # Subtype is immutable — a training belongs to its scope for life. Only the
    # title and the item tree can change.
    title = body.title.strip() if body.title else None
    training.title = title or None
    # Replace the item list wholesale with the submitted (ordered) one.
    training.items = _build_items(body.items)
    await session.commit()

    reloaded = await _load_with_items(session, training_id)
    assert reloaded is not None
    return reloaded


@router.patch("/{training_id}/position", response_model=CardioTrainingResponse)
async def reorder_cardio_training(
    training_id: uuid.UUID,
    body: UpdateCardioPositionRequest,
    _admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CardioTraining:
    """Move a cardio training to a new 0-based position within its subtype; the rest
    of the subtype shifts to stay a contiguous 0..n-1 sequence."""
    training = await session.get(CardioTraining, training_id)
    if training is None:
        raise api_error(
            status.HTTP_404_NOT_FOUND,
            ErrorCode.cardio_training_not_found,
            "Cardio training not found",
        )

    # All trainings in this subtype, in current order.
    scope = list(
        await session.scalars(
            select(CardioTraining)
            .where(CardioTraining.subtype == training.subtype)
            .order_by(CardioTraining.position)
        )
    )

    # Re-insert the moved training at the clamped target index, then renumber.
    target = max(0, min(body.position, len(scope) - 1))
    scope.remove(training)
    scope.insert(target, training)
    for index, item in enumerate(scope):
        item.position = index
    # The deferrable unique constraint is checked at commit, so the renumber above
    # can transiently repeat positions without erroring.
    await session.commit()
    await session.refresh(training)
    return training


@router.delete("/{training_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cardio_training(
    training_id: uuid.UUID,
    _admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    training = await session.get(CardioTraining, training_id)
    if training is None:
        raise api_error(
            status.HTTP_404_NOT_FOUND,
            ErrorCode.cardio_training_not_found,
            "Cardio training not found",
        )
    await session.delete(training)
    await session.commit()
