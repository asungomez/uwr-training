import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_serializer

from app.models import TrainingCategory, TrainingSubtype
from app.pagination import PaginationParams


class SubBlockInput(BaseModel):
    name: str
    notes: str | None = None


class BlockInput(BaseModel):
    name: str
    sub_blocks: list[SubBlockInput] = []


class CreateTrainingRequest(BaseModel):
    category: TrainingCategory
    subtype: TrainingSubtype
    title: str | None = None
    blocks: list[BlockInput] = []


class UpdateTrainingRequest(BaseModel):
    category: TrainingCategory
    subtype: TrainingSubtype
    title: str | None = None
    blocks: list[BlockInput] = []


class TrainingListParams(PaginationParams):
    """Query params for the trainings list: pagination + filters."""

    search: str | None = None
    category: TrainingCategory | None = None
    subtype: TrainingSubtype | None = None


class TrainingSessionResponse(BaseModel):
    """List view: the session itself, without its block tree."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category: TrainingCategory
    subtype: TrainingSubtype
    title: str | None
    created_at: datetime

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)


class SubBlockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    notes: str | None

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)


class BlockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    sub_blocks: list[SubBlockResponse] = []

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)


class TrainingSessionDetailResponse(TrainingSessionResponse):
    """Detail view: the session plus its ordered blocks."""

    blocks: list[BlockResponse] = []
