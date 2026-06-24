import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_serializer

from app.models import CardioIntervalKind, CardioItemKind, CardioSubtype
from app.pagination import PaginationParams


class IntervalInput(BaseModel):
    """One step of a block's round: an `effort` (duration + intensity %) or a
    `rest` (duration only)."""

    kind: Literal["effort", "rest"]
    duration_seconds: int
    # effort only — percentage of max effort (60, 80, …). Ignored for rests.
    intensity_pct: int | None = None


class CardioItemInput(BaseModel):
    """One entry in a cardio training. A `note` carries free text; a `block` is a
    round (its intervals) repeated `repeats` times, with an optional trailing rest."""

    kind: Literal["note", "block"]
    text: str | None = None
    # block only.
    repeats: int = 1
    rest_seconds: int | None = None
    intervals: list[IntervalInput] = []


class CreateCardioTrainingRequest(BaseModel):
    subtype: CardioSubtype
    title: str | None = None
    items: list[CardioItemInput] = []


class UpdateCardioTrainingRequest(BaseModel):
    # Subtype is immutable, so it's not accepted here — only title + items change.
    title: str | None = None
    items: list[CardioItemInput] = []


class UpdateCardioPositionRequest(BaseModel):
    """Move a cardio training to a new 0-based position within its subtype; the
    others in that subtype shift to keep a contiguous order."""

    position: int


class CardioListParams(PaginationParams):
    """Query params for the cardio list: pagination + filters."""

    search: str | None = None
    subtype: CardioSubtype | None = None


class CardioTrainingResponse(BaseModel):
    """List view: the training itself, without its item tree."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subtype: CardioSubtype
    position: int
    title: str | None
    created_at: datetime

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)


class IntervalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: CardioIntervalKind
    duration_seconds: int
    intensity_pct: int | None = None

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)


class CardioItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: CardioItemKind
    text: str | None = None
    # block only.
    repeats: int = 1
    rest_seconds: int | None = None
    intervals: list[IntervalResponse] = []

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)


class CardioTrainingDetailResponse(CardioTrainingResponse):
    """Detail view: the training plus its ordered items (blocks + notes)."""

    items: list[CardioItemResponse] = []
