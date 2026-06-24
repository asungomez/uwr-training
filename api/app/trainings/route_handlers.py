import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import current_user, require_admin
from app.db import get_session
from app.errors import ErrorCode, api_error
from app.models import SUBTYPES_BY_CATEGORY, TrainingSession, User
from app.pagination import Page
from app.trainings.schemas import (
    CreateTrainingRequest,
    TrainingListParams,
    TrainingSessionResponse,
)

router = APIRouter(prefix="/trainings", tags=["trainings"])


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


@router.get("/{training_id}", response_model=TrainingSessionResponse)
async def get_training(
    training_id: uuid.UUID,
    _user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TrainingSession:
    """A single training session by id. Visible to any authenticated user."""
    training = await session.get(TrainingSession, training_id)
    if training is None:
        raise api_error(
            status.HTTP_404_NOT_FOUND,
            ErrorCode.training_not_found,
            "Training not found",
        )
    return training


@router.post("", response_model=TrainingSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_training(
    body: CreateTrainingRequest,
    _admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TrainingSession:
    if body.subtype not in SUBTYPES_BY_CATEGORY[body.category]:
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            ErrorCode.invalid_training_subtype,
            f"Subtype {body.subtype.value} is not valid for category {body.category.value}",
        )

    title = body.title.strip() if body.title else None
    training = TrainingSession(category=body.category, subtype=body.subtype, title=title or None)
    session.add(training)
    await session.commit()
    await session.refresh(training)
    return training
