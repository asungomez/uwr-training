import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_serializer

from app.models import TrainingCategory, TrainingItemKind, TrainingSubtype
from app.pagination import PaginationParams


class ItemInput(BaseModel):
    """One entry in a sub-block. A `note` carries free text; a `series` carries an
    exercise plus an all-optional prescription (sets/reps/time/distance/effort)."""

    kind: Literal["note", "series"]
    text: str | None = None
    # series only — the exercise is required, the rest are optional.
    exercise_id: uuid.UUID | None = None
    sets: int | None = None
    reps: int | None = None
    duration_seconds: int | None = None
    distance_meters: int | None = None
    effort: str | None = None
    # Load as a % (out of 100, may be fractional) of the athlete's latest
    # strength-test result for this exercise.
    load_percentage: float | None = None


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
    # Category and subtype are immutable, so they're not accepted here — only the
    # title and the block tree can change.
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
    # When the requesting athlete last logged this session (their own logs only);
    # null if they never have.
    last_performed_at: datetime | None = None

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)


class ItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: TrainingItemKind
    text: str | None
    # series only — the exercise (id + name, for rendering and round-tripping) plus
    # its prescription. All null for notes (and unset series fields).
    exercise_id: uuid.UUID | None = None
    exercise_name: str | None = None
    sets: int | None = None
    reps: int | None = None
    duration_seconds: int | None = None
    distance_meters: int | None = None
    effort: str | None = None
    # Target load as a % (out of 100, may be fractional) of the latest strength-test
    # result for this exercise. The absolute kg is computed per-athlete by the client.
    load_percentage: float | None = None

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)

    @field_serializer("exercise_id")
    def serialize_exercise_id(self, value: uuid.UUID | None) -> str | None:
        return str(value) if value is not None else None


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
