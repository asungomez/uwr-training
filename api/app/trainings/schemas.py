import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_serializer

from app.models import TrainingCategory, TrainingSubtype


class CreateTrainingRequest(BaseModel):
    category: TrainingCategory
    subtype: TrainingSubtype
    title: str | None = None


class TrainingSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category: TrainingCategory
    subtype: TrainingSubtype
    title: str | None
    created_at: datetime

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)
