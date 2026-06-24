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
    TrainingSession,
    TrainingSubtype,
    User,
)
from app.pagination import Page
from app.trainings.schemas import (
    BlockInput,
    CreateTrainingRequest,
    TrainingListParams,
    TrainingSessionDetailResponse,
    TrainingSessionResponse,
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
    """Build ordered TrainingBlock rows from the submitted list (its order defines
    position). Rejects blank names."""
    rows: list[TrainingBlock] = []
    for position, item in enumerate(blocks):
        name = item.name.strip()
        if not name:
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.invalid_block,
                "Block name is required",
            )
        rows.append(TrainingBlock(name=name, position=position))
    return rows


async def _load_with_blocks(
    session: AsyncSession, training_id: uuid.UUID
) -> TrainingSession | None:
    """Fetch a session with its blocks (ordered) loaded."""
    training: TrainingSession | None = await session.scalar(
        select(TrainingSession)
        .where(TrainingSession.id == training_id)
        .options(selectinload(TrainingSession.blocks))
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
        .order_by(TrainingSession.created_at.desc())
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
    training = TrainingSession(category=body.category, subtype=body.subtype, title=title or None)
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
