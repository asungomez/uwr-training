import uuid
from datetime import datetime

from pydantic import BaseModel, field_serializer

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


class WeekLogSummary(BaseModel):
    """A session log (of the requesting athlete) that counts towards a requirement."""

    log_id: uuid.UUID
    training_session_id: uuid.UUID
    training_title: str | None
    performed_at: datetime

    @field_serializer("log_id", "training_session_id")
    def serialize_ids(self, value: uuid.UUID) -> str:
        return str(value)


class RequirementProgress(BaseModel):
    """A requirement plus how many of the athlete's logs (linked to this week) fulfil
    it — e.g. 1/2 endurance pools done."""

    id: uuid.UUID
    category: TrainingCategory
    subtype: TrainingSubtype
    count: int
    completed: int

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)


class RequirementDetail(RequirementProgress):
    """A requirement with progress plus the logs (most recent first) that fulfil it."""

    logs: list[WeekLogSummary] = []


class WeekResponse(BaseModel):
    """List view: the week with its requirements + the athlete's progress on each."""

    id: uuid.UUID
    name: str
    position: int
    recommended_date: str | None
    phase: MesocyclePhase
    created_at: datetime
    requirements: list[RequirementProgress] = []

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)


class WeekDetailResponse(BaseModel):
    """Detail view: each requirement carries its progress plus the logs that fulfil
    it (the requesting athlete's own)."""

    id: uuid.UUID
    name: str
    position: int
    recommended_date: str | None
    phase: MesocyclePhase
    created_at: datetime
    requirements: list[RequirementDetail] = []

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)
