from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.db import get_session
from app.errors import ErrorCode, api_error
from app.exercises.schemas import CreateExerciseRequest, ExerciseResponse
from app.models import Exercise, User

router = APIRouter(prefix="/exercises", tags=["exercises"])


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
