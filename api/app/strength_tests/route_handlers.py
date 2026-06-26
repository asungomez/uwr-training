from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import current_user, require_admin
from app.db import get_session
from app.errors import ErrorCode, api_error
from app.models import Exercise, ExerciseType, StrengthTestItem, User
from app.strength_tests.schemas import (
    StrengthTestItemResponse,
    StrengthTestResponse,
    UpdateStrengthTestRequest,
)

# The strength test is a single global config (one ordered set of exercises), so
# there's no id in the path — the whole resource is "the strength test".
router = APIRouter(prefix="/strength-test", tags=["strength-test"])


async def _load_items(session: AsyncSession) -> list[StrengthTestItem]:
    """The strength test's items in order, each with its exercise loaded."""
    rows = await session.scalars(
        select(StrengthTestItem)
        .order_by(StrengthTestItem.position)
        .options(selectinload(StrengthTestItem.exercise))
    )
    return list(rows.all())


def _response(items: list[StrengthTestItem]) -> StrengthTestResponse:
    return StrengthTestResponse(
        items=[
            StrengthTestItemResponse(
                id=item.id,
                exercise_id=item.exercise_id,
                exercise_name=item.exercise.name,
                weight_multiplier=item.weight_multiplier,
            )
            for item in items
        ]
    )


@router.get("", response_model=StrengthTestResponse)
async def get_strength_test(
    _user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> StrengthTestResponse:
    """The strength test: its ordered exercises and their body-weight multipliers."""
    return _response(await _load_items(session))


@router.put("", response_model=StrengthTestResponse)
async def update_strength_test(
    body: UpdateStrengthTestRequest,
    _admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> StrengthTestResponse:
    """Replace the whole strength test with the submitted ordered list. Each item
    must point to an existing gym exercise and carry a positive multiplier."""
    exercise_ids = [item.exercise_id for item in body.items]
    if len(set(exercise_ids)) != len(exercise_ids):
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            ErrorCode.invalid_strength_test,
            "An exercise can't appear twice in the strength test",
        )

    # Validate every exercise exists and is a gym exercise.
    exercises = {
        exercise.id: exercise
        for exercise in (
            await session.scalars(select(Exercise).where(Exercise.id.in_(exercise_ids)))
        ).all()
    }
    for item in body.items:
        exercise = exercises.get(item.exercise_id)
        if exercise is None or exercise.type is not ExerciseType.gym:
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.invalid_strength_test,
                "Each item must be an existing gym exercise",
            )
        if item.weight_multiplier <= 0:
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.invalid_strength_test,
                "The weight multiplier must be greater than 0",
            )

    # Replace the whole ordered set.
    await session.execute(delete(StrengthTestItem))
    for position, item in enumerate(body.items):
        session.add(
            StrengthTestItem(
                position=position,
                exercise_id=item.exercise_id,
                weight_multiplier=item.weight_multiplier,
            )
        )
    await session.commit()

    return _response(await _load_items(session))
