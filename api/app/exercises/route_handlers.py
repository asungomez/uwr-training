from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import current_user, require_admin
from app.db import get_session
from app.errors import ErrorCode, api_error
from app.exercises.schemas import (
    CreateExerciseRequest,
    ExerciseListParams,
    ExerciseResponse,
)
from app.models import Exercise, User
from app.pagination import Page

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("")
async def list_exercises(
    _user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    params: Annotated[ExerciseListParams, Query()],
) -> Page[ExerciseResponse]:
    """All exercises, filterable by name search and type. Visible to any user."""
    filters: list[ColumnElement[bool]] = []
    if params.search:
        filters.append(Exercise.name.ilike(f"%{params.search.strip()}%"))
    if params.type is not None:
        filters.append(Exercise.type == params.type)

    total = await session.scalar(select(func.count()).select_from(Exercise).where(*filters))
    rows = await session.scalars(
        select(Exercise)
        .where(*filters)
        .order_by(Exercise.name)
        .offset(params.offset)
        .limit(params.page_size)
    )
    return Page(
        items=[ExerciseResponse.model_validate(row) for row in rows.all()],
        total_count=total or 0,
    )


@router.post("", response_model=ExerciseResponse, status_code=status.HTTP_201_CREATED)
async def create_exercise(
    body: CreateExerciseRequest,
    _admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Exercise:
    name = body.name.strip()

    existing = await session.scalar(select(Exercise).where(Exercise.name == name))
    if existing is not None:
        raise api_error(
            status.HTTP_409_CONFLICT,
            ErrorCode.exercise_already_exists,
            "An exercise with this name already exists",
        )

    description = body.description.strip() if body.description else None
    exercise = Exercise(name=name, description=description or None, type=body.type)
    session.add(exercise)
    await session.commit()
    await session.refresh(exercise)
    return exercise
