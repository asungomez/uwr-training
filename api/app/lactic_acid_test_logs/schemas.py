import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_serializer

from app.trainings.schemas import TrainingSessionDetailResponse


class LacticAcidTestLogFormWeek(BaseModel):
    """A calendar week the athlete can assign a lactic-acid-test log to."""

    id: uuid.UUID
    name: str

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)


class LacticAcidTestLogFormResponse(BaseModel):
    """What the athlete needs to take the lactic-acid test: the warmup session (shown
    read-only) plus the assignable weeks and the recommended one to pre-select."""

    warmup: TrainingSessionDetailResponse
    weeks: list[LacticAcidTestLogFormWeek] = []
    recommended_week_id: uuid.UUID | None = None

    @field_serializer("recommended_week_id")
    def serialize_recommended(self, value: uuid.UUID | None) -> str | None:
        return str(value) if value is not None else None


class CreateLacticAcidTestLogRequest(BaseModel):
    """Record either measure of the lactic-acid test (or both). `personal_best` is the
    single 50 m max-effort time; `test_result` is the average over 8 repetitions. Both
    are optional seconds (with decimals), but at least one must be present. Each saved
    one becomes its own log, sharing the optional week."""

    personal_best: float | None = None
    test_result: float | None = None
    week_id: uuid.UUID | None = None


class LacticAcidTestLogResponse(BaseModel):
    """A single lactic-acid-test log (personal best or test result)."""

    id: uuid.UUID
    kind: Literal["personal-best", "test-result"]
    performed_at: datetime
    seconds: float
    week_id: uuid.UUID | None
    week_name: str | None

    @field_serializer("id", "week_id")
    def serialize_ids(self, value: uuid.UUID | None) -> str | None:
        return str(value) if value is not None else None


class CreateLacticAcidTestLogResponse(BaseModel):
    """The logs created from one submission — the personal best, the test result, or
    both, whichever the athlete filled in."""

    personal_best: LacticAcidTestLogResponse | None = None
    test_result: LacticAcidTestLogResponse | None = None


class LacticAcidTestLogSummaryResponse(BaseModel):
    """List view of a lactic-acid-test log: when it was done and the time."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    performed_at: datetime
    seconds: float

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)
