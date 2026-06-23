import uuid
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
    MediaUploadRequest,
    MediaUploadResponse,
    UpdateExerciseRequest,
)
from app.models import Exercise, User
from app.pagination import Page
from app.storage import MEDIA_CONSTRAINTS, create_presigned_upload

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.post("/media-uploads", response_model=MediaUploadResponse)
async def create_media_upload(
    body: MediaUploadRequest,
    _admin: Annotated[User, Depends(require_admin)],
) -> MediaUploadResponse:
    """Mint a presigned POST so the admin's browser can upload a thumbnail or
    video straight to S3. Returns the object key to store on save."""
    allowed_types, _max_size = MEDIA_CONSTRAINTS[body.kind]
    if body.content_type not in allowed_types:
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            ErrorCode.invalid_media_type,
            f"Unsupported content type for {body.kind.value}",
        )
    upload = create_presigned_upload(body.kind, body.content_type)
    return MediaUploadResponse(key=upload.key, url=upload.url, fields=upload.fields)


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


@router.get("/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise(
    exercise_id: uuid.UUID,
    _user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Exercise:
    """A single exercise by id. Visible to any authenticated user."""
    exercise = await session.get(Exercise, exercise_id)
    if exercise is None:
        raise api_error(
            status.HTTP_404_NOT_FOUND,
            ErrorCode.exercise_not_found,
            "Exercise not found",
        )
    return exercise


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
    exercise = Exercise(
        name=name,
        description=description or None,
        type=body.type,
        thumbnail_key=body.thumbnail_key,
        video_key=body.video_key,
    )
    session.add(exercise)
    await session.commit()
    await session.refresh(exercise)
    return exercise


@router.put("/{exercise_id}", response_model=ExerciseResponse)
async def update_exercise(
    exercise_id: uuid.UUID,
    body: UpdateExerciseRequest,
    _admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Exercise:
    exercise = await session.get(Exercise, exercise_id)
    if exercise is None:
        raise api_error(
            status.HTTP_404_NOT_FOUND,
            ErrorCode.exercise_not_found,
            "Exercise not found",
        )

    name = body.name.strip()
    clash = await session.scalar(
        select(Exercise).where(Exercise.name == name, Exercise.id != exercise_id)
    )
    if clash is not None:
        raise api_error(
            status.HTTP_409_CONFLICT,
            ErrorCode.exercise_already_exists,
            "An exercise with this name already exists",
        )

    description = body.description.strip() if body.description else None
    exercise.name = name
    exercise.description = description or None
    exercise.type = body.type
    # The request carries the desired final keys (kept, replaced, or cleared).
    exercise.thumbnail_key = body.thumbnail_key
    exercise.video_key = body.video_key
    await session.commit()
    await session.refresh(exercise)
    return exercise


@router.delete("/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exercise(
    exercise_id: uuid.UUID,
    _admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    exercise = await session.get(Exercise, exercise_id)
    if exercise is None:
        raise api_error(
            status.HTTP_404_NOT_FOUND,
            ErrorCode.exercise_not_found,
            "Exercise not found",
        )
    await session.delete(exercise)
    await session.commit()
