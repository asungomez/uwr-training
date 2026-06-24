from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.db import get_session
from app.errors import ErrorCode, api_error
from app.models import SUBTYPES_BY_CATEGORY, TrainingSession, User
from app.trainings.schemas import CreateTrainingRequest, TrainingSessionResponse

router = APIRouter(prefix="/trainings", tags=["trainings"])


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
