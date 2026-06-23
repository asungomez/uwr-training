import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_serializer

from app.models import ExerciseType
from app.pagination import PaginationParams


class CreateExerciseRequest(BaseModel):
    name: str
    description: str | None = None
    type: ExerciseType


class UpdateExerciseRequest(BaseModel):
    name: str
    description: str | None = None
    type: ExerciseType


class ExerciseListParams(PaginationParams):
    """Query params for the exercises directory: pagination + filters."""

    search: str | None = None
    type: ExerciseType | None = None


class ExerciseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    type: ExerciseType
    created_at: datetime

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)
