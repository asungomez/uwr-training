import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import current_user, require_admin
from app.db import get_session
from app.errors import ErrorCode, api_error
from app.models import (
    SUBTYPES_BY_CATEGORY,
    TrainingBlock,
    TrainingCategory,
    TrainingItem,
    TrainingItemKind,
    TrainingSession,
    TrainingSubBlock,
    TrainingSubtype,
    User,
)
from app.pagination import Page
from app.trainings.schemas import (
    BlockInput,
    CreateTrainingRequest,
    ItemInput,
    SubBlockInput,
    TrainingListParams,
    TrainingSessionDetailResponse,
    TrainingSessionResponse,
    UpdatePositionRequest,
    UpdateTrainingRequest,
)

router = APIRouter(prefix="/trainings", tags=["trainings"])


def _validate_subtype(category: TrainingCategory, subtype: TrainingSubtype) -> None:
    """Reject a subtype that doesn't belong to the category."""
    if subtype not in SUBTYPES_BY_CATEGORY[category]:
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            ErrorCode.invalid_training_subtype,
            f"Subtype {subtype.value} is not valid for category {category.value}",
        )


def _build_blocks(blocks: list[BlockInput]) -> list[TrainingBlock]:
    """Build ordered TrainingBlock rows (with their sub-blocks) from the submitted
    list — its order defines position. Rejects blank block/sub-block names."""
    rows: list[TrainingBlock] = []
    for position, item in enumerate(blocks):
        name = item.name.strip()
        if not name:
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.invalid_block,
                "Block name is required",
            )
        rows.append(
            TrainingBlock(
                name=name, position=position, sub_blocks=_build_sub_blocks(item.sub_blocks)
            )
        )
    return rows


def _build_sub_blocks(sub_blocks: list[SubBlockInput]) -> list[TrainingSubBlock]:
    """Build ordered TrainingSubBlock rows (with their items) from the submitted
    list. Rejects blank names."""
    rows: list[TrainingSubBlock] = []
    for position, item in enumerate(sub_blocks):
        name = item.name.strip()
        if not name:
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.invalid_block,
                "Sub-block name is required",
            )
        notes = item.notes.strip() if item.notes else None
        rows.append(
            TrainingSubBlock(
                name=name, position=position, notes=notes or None, items=_build_items(item.items)
            )
        )
    return rows


def _build_items(items: list[ItemInput]) -> list[TrainingItem]:
    """Build ordered TrainingItem rows from the submitted list (just notes for now)."""
    rows: list[TrainingItem] = []
    for position, item in enumerate(items):
        text = item.text.strip() if item.text else None
        rows.append(TrainingItem(kind=TrainingItemKind.note, position=position, text=text or None))
    return rows


async def _next_position(
    session: AsyncSession, category: TrainingCategory, subtype: TrainingSubtype
) -> int:
    """The next free position at the end of a category+subtype scope."""
    max_position = await session.scalar(
        select(func.max(TrainingSession.position)).where(
            TrainingSession.category == category,
            TrainingSession.subtype == subtype,
        )
    )
    return 0 if max_position is None else max_position + 1


async def _load_with_blocks(
    session: AsyncSession, training_id: uuid.UUID
) -> TrainingSession | None:
    """Fetch a session with its blocks, sub-blocks, and items (ordered) loaded."""
    training: TrainingSession | None = await session.scalar(
        select(TrainingSession)
        .where(TrainingSession.id == training_id)
        .options(
            selectinload(TrainingSession.blocks)
            .selectinload(TrainingBlock.sub_blocks)
            .selectinload(TrainingSubBlock.items)
        )
    )
    return training


@router.get("")
async def list_trainings(
    _user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    params: Annotated[TrainingListParams, Query()],
) -> Page[TrainingSessionResponse]:
    """All training sessions, filterable by title search, category and subtype.
    Visible to any authenticated user."""
    filters: list[ColumnElement[bool]] = []
    if params.search:
        filters.append(TrainingSession.title.ilike(f"%{params.search.strip()}%"))
    if params.category is not None:
        filters.append(TrainingSession.category == params.category)
    if params.subtype is not None:
        filters.append(TrainingSession.subtype == params.subtype)

    total = await session.scalar(select(func.count()).select_from(TrainingSession).where(*filters))
    rows = await session.scalars(
        select(TrainingSession)
        .where(*filters)
        .order_by(TrainingSession.position)
        .offset(params.offset)
        .limit(params.page_size)
    )
    return Page(
        items=[TrainingSessionResponse.model_validate(row) for row in rows.all()],
        total_count=total or 0,
    )


@router.get("/{training_id}", response_model=TrainingSessionDetailResponse)
async def get_training(
    training_id: uuid.UUID,
    _user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TrainingSession:
    """A single training session (with its blocks) by id. Visible to any user."""
    training = await _load_with_blocks(session, training_id)
    if training is None:
        raise api_error(
            status.HTTP_404_NOT_FOUND,
            ErrorCode.training_not_found,
            "Training not found",
        )
    return training


@router.post("", response_model=TrainingSessionDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_training(
    body: CreateTrainingRequest,
    _admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TrainingSession:
    _validate_subtype(body.category, body.subtype)

    title = body.title.strip() if body.title else None
    training = TrainingSession(
        category=body.category,
        subtype=body.subtype,
        position=await _next_position(session, body.category, body.subtype),
        title=title or None,
    )
    training.blocks = _build_blocks(body.blocks)
    session.add(training)
    await session.commit()

    reloaded = await _load_with_blocks(session, training.id)
    assert reloaded is not None
    return reloaded


@router.put("/{training_id}", response_model=TrainingSessionDetailResponse)
async def update_training(
    training_id: uuid.UUID,
    body: UpdateTrainingRequest,
    _admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TrainingSession:
    training = await _load_with_blocks(session, training_id)
    if training is None:
        raise api_error(
            status.HTTP_404_NOT_FOUND,
            ErrorCode.training_not_found,
            "Training not found",
        )
    _validate_subtype(body.category, body.subtype)

    # If the scope changed, move it to the end of the new one so its old position
    # can't collide there.
    if training.category != body.category or training.subtype != body.subtype:
        training.position = await _next_position(session, body.category, body.subtype)

    title = body.title.strip() if body.title else None
    training.category = body.category
    training.subtype = body.subtype
    training.title = title or None
    # Replace the block list wholesale with the submitted (ordered) one.
    training.blocks = _build_blocks(body.blocks)
    await session.commit()

    reloaded = await _load_with_blocks(session, training_id)
    assert reloaded is not None
    return reloaded


@router.patch("/{training_id}/position", response_model=TrainingSessionResponse)
async def reorder_training(
    training_id: uuid.UUID,
    body: UpdatePositionRequest,
    _admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TrainingSession:
    """Move a training to a new 0-based position within its category+subtype; the
    rest of the scope shifts to stay a contiguous 0..n-1 sequence."""
    training = await session.get(TrainingSession, training_id)
    if training is None:
        raise api_error(
            status.HTTP_404_NOT_FOUND,
            ErrorCode.training_not_found,
            "Training not found",
        )

    # All sessions in this scope, in current order.
    scope = list(
        await session.scalars(
            select(TrainingSession)
            .where(
                TrainingSession.category == training.category,
                TrainingSession.subtype == training.subtype,
            )
            .order_by(TrainingSession.position)
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
async def delete_training(
    training_id: uuid.UUID,
    _admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    training = await session.get(TrainingSession, training_id)
    if training is None:
        raise api_error(
            status.HTTP_404_NOT_FOUND,
            ErrorCode.training_not_found,
            "Training not found",
        )
    await session.delete(training)
    await session.commit()
