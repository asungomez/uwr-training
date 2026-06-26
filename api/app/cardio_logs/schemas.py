import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_serializer


class CardioLogFormWeek(BaseModel):
    """A calendar week the athlete can assign this cardio log to."""

    id: uuid.UUID
    name: str

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)


class CardioLogFormResponse(BaseModel):
    """What the 'log cardio session' form needs: the title and the weeks this
    session can be assigned to, plus the recommended one to pre-select."""

    cardio_training_id: uuid.UUID
    title: str | None
    weeks: list[CardioLogFormWeek] = []
    recommended_week_id: uuid.UUID | None = None

    @field_serializer("cardio_training_id", "recommended_week_id")
    def serialize_ids(self, value: uuid.UUID | None) -> str | None:
        return str(value) if value is not None else None


class CreateCardioLogRequest(BaseModel):
    # The specific cardio activity done (free text), an optional note, and the week.
    exercise: str | None = None
    note: str | None = None
    week_id: uuid.UUID | None = None


class UpdateCardioLogWeekRequest(BaseModel):
    """Change (or clear) which calendar week a cardio log counts towards."""

    week_id: uuid.UUID | None = None


class CardioLogResponse(BaseModel):
    id: uuid.UUID
    cardio_training_id: uuid.UUID
    performed_at: datetime
    exercise: str | None
    note: str | None
    week_id: uuid.UUID | None
    week_name: str | None

    @field_serializer("id", "cardio_training_id", "week_id")
    def serialize_ids(self, value: uuid.UUID | None) -> str | None:
        return str(value) if value is not None else None


class CardioLogSummaryResponse(BaseModel):
    """List view of a cardio log: the date, exercise, and note."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    performed_at: datetime
    exercise: str | None
    note: str | None

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)
