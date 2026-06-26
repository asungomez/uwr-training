import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_serializer


class StrengthTestLogFormWeek(BaseModel):
    """A calendar week the athlete can assign this strength-test log to."""

    id: uuid.UUID
    name: str

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)


class StrengthTestLogFormExercise(BaseModel):
    """One exercise to perform in the test, with the target load computed from the
    athlete's latest body weight x the exercise's multiplier."""

    exercise_id: uuid.UUID
    exercise_name: str
    weight_multiplier: float
    target_weight_kg: float

    @field_serializer("exercise_id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)


class StrengthTestLogFormResponse(BaseModel):
    """Everything the athlete needs to take the test: the reference body weight, the
    exercises with their target loads, and the assignable weeks (+ recommended one)."""

    bodyweight_kg: float
    exercises: list[StrengthTestLogFormExercise] = []
    weeks: list[StrengthTestLogFormWeek] = []
    recommended_week_id: uuid.UUID | None = None

    @field_serializer("recommended_week_id")
    def serialize_recommended(self, value: uuid.UUID | None) -> str | None:
        return str(value) if value is not None else None


class StrengthTestLogEntryInput(BaseModel):
    """The weight the athlete actually lifted for one exercise of the test."""

    exercise_id: uuid.UUID
    actual_weight_kg: float


class CreateStrengthTestLogRequest(BaseModel):
    entries: list[StrengthTestLogEntryInput] = []
    week_id: uuid.UUID | None = None


class UpdateStrengthTestLogWeekRequest(BaseModel):
    """Change (or clear) which calendar week a strength-test log counts towards."""

    week_id: uuid.UUID | None = None


class StrengthTestLogEntryResponse(BaseModel):
    exercise_id: uuid.UUID
    exercise_name: str
    target_weight_kg: float
    actual_weight_kg: float

    @field_serializer("exercise_id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)


class StrengthTestLogResponse(BaseModel):
    id: uuid.UUID
    performed_at: datetime
    bodyweight_kg: float
    week_id: uuid.UUID | None
    week_name: str | None
    entries: list[StrengthTestLogEntryResponse] = []

    @field_serializer("id", "week_id")
    def serialize_ids(self, value: uuid.UUID | None) -> str | None:
        return str(value) if value is not None else None


class StrengthTestLogSummaryResponse(BaseModel):
    """List view of a strength-test log: just when it was taken and the reference weight."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    performed_at: datetime
    bodyweight_kg: float

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)
