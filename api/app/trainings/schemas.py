import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_serializer

from app.models import TrainingCategory, TrainingItemKind, TrainingSubtype
from app.pagination import PaginationParams


class ItemInput(BaseModel):
    # Only notes for now; series will extend this later.
    kind: Literal["note"]
    text: str | None = None


class SubBlockInput(BaseModel):
    name: str
    notes: str | None = None
    items: list[ItemInput] = []


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


class UpdatePositionRequest(BaseModel):
    """Move a training to a new 0-based position within its category+subtype; the
    others in that scope shift to keep a contiguous order."""

    position: int


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
    position: int
    title: str | None
    created_at: datetime

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)


class ItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: TrainingItemKind
    text: str | None

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)


class SubBlockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    notes: str | None
    items: list[ItemResponse] = []

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
