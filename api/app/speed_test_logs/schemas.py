import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_serializer

from app.trainings.schemas import TrainingSessionDetailResponse


class SpeedTestLogFormWeek(BaseModel):
    """A calendar week the athlete can assign this speed-test log to."""

    id: uuid.UUID
    name: str

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)


class SpeedTestLogFormResponse(BaseModel):
    """What the athlete needs to take the speed test: the warmup session (shown
    read-only) plus the assignable weeks and the recommended one to pre-select."""

    warmup: TrainingSessionDetailResponse
    weeks: list[SpeedTestLogFormWeek] = []
    recommended_week_id: uuid.UUID | None = None

    @field_serializer("recommended_week_id")
    def serialize_recommended(self, value: uuid.UUID | None) -> str | None:
        return str(value) if value is not None else None


class CreateSpeedTestLogRequest(BaseModel):
    # The 25 m time in seconds (with decimals, e.g. 11.5), and the optional week.
    seconds: float
    week_id: uuid.UUID | None = None


class UpdateSpeedTestLogWeekRequest(BaseModel):
    """Change (or clear) which calendar week a speed-test log counts towards."""

    week_id: uuid.UUID | None = None


class SpeedTestLogResponse(BaseModel):
    id: uuid.UUID
    performed_at: datetime
    seconds: float
    week_id: uuid.UUID | None
    week_name: str | None

    @field_serializer("id", "week_id")
    def serialize_ids(self, value: uuid.UUID | None) -> str | None:
        return str(value) if value is not None else None


class SpeedTestLogSummaryResponse(BaseModel):
    """List view of a speed-test log: when it was done and the time."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    performed_at: datetime
    seconds: float

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)
