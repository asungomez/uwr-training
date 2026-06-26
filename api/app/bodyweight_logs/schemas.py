import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_serializer


class CreateBodyweightLogRequest(BaseModel):
    """Record the athlete's current body weight, in kilograms."""

    weight_kg: float


class BodyweightLogResponse(BaseModel):
    """One body-weight measurement: the value in kilos and when it was recorded."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    weight_kg: float
    recorded_at: datetime

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)
