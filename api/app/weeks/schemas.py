import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_serializer

from app.models import MesocyclePhase, TrainingCategory, TrainingSubtype
from app.pagination import PaginationParams


class RequirementInput(BaseModel):
    """How many sessions of one type a week recommends, e.g. 2x pool/endurance."""

    category: TrainingCategory
    subtype: TrainingSubtype
    count: int


class CreateWeekRequest(BaseModel):
    name: str
    recommended_date: str | None = None
    phase: MesocyclePhase
    requirements: list[RequirementInput] = []


class UpdateWeekRequest(BaseModel):
    name: str
    recommended_date: str | None = None
    phase: MesocyclePhase
    requirements: list[RequirementInput] = []


class UpdateWeekPositionRequest(BaseModel):
    """Move a week to a new 0-based position; the others shift to keep order."""

    position: int


class WeekListParams(PaginationParams):
    """Query params for the weeks list: pagination + filters."""

    search: str | None = None
    phase: MesocyclePhase | None = None


class RequirementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category: TrainingCategory
    subtype: TrainingSubtype
    count: int

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)


class WeekResponse(BaseModel):
    """List view: the week itself, without its requirements."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    position: int
    recommended_date: str | None
    phase: MesocyclePhase
    created_at: datetime

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)


class WeekDetailResponse(WeekResponse):
    """Detail view: the week plus its ordered session requirements."""

    requirements: list[RequirementResponse] = []
