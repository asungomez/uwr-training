import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_serializer

from app.models import SessionLogAction

# ---- log form (what the athlete fills in) -----------------------------------


class LogFormAlternative(BaseModel):
    """An alternative exercise the athlete may pick instead of the prescribed one."""

    exercise_id: uuid.UUID
    name: str

    @field_serializer("exercise_id")
    def serialize_exercise_id(self, value: uuid.UUID) -> str:
        return str(value)


class LogFormParameter(BaseModel):
    parameter_id: uuid.UUID
    name: str

    @field_serializer("parameter_id")
    def serialize_parameter_id(self, value: uuid.UUID) -> str:
        return str(value)


class LogFormExercise(BaseModel):
    """One series item's exercise in the log form: the prescribed exercise plus the
    alternatives it can be swapped for and the parameters the athlete can record."""

    exercise_id: uuid.UUID
    name: str
    alternatives: list[LogFormAlternative] = []
    parameters: list[LogFormParameter] = []

    @field_serializer("exercise_id")
    def serialize_exercise_id(self, value: uuid.UUID) -> str:
        return str(value)


class LogFormResponse(BaseModel):
    """Everything needed to render the 'start session' form: the session's exercises
    (in order), each with its alternatives and trackable parameters."""

    training_id: uuid.UUID
    title: str | None
    exercises: list[LogFormExercise] = []

    @field_serializer("training_id")
    def serialize_training_id(self, value: uuid.UUID) -> str:
        return str(value)


# ---- log submission ----------------------------------------------------------


class ParameterValueInput(BaseModel):
    parameter_id: uuid.UUID
    value: str


class LogEntryInput(BaseModel):
    """One series item the athlete went through: marked done or skipped. When done,
    `performed_exercise_id` is the exercise actually used (the prescribed one or a
    chosen alternative) and `parameter_values` are the values recorded for it."""

    # The series item's prescribed exercise (validates the item + the swap).
    planned_exercise_id: uuid.UUID
    action: Literal["done", "skipped"]
    # Required when action == done; ignored when skipped.
    performed_exercise_id: uuid.UUID | None = None
    parameter_values: list[ParameterValueInput] = []


class CreateSessionLogRequest(BaseModel):
    note: str | None = None
    entries: list[LogEntryInput] = []


# ---- log read-back (returned on create) -------------------------------------


class LogParameterValueResponse(BaseModel):
    id: uuid.UUID
    parameter_id: uuid.UUID
    name: str
    value: str

    @field_serializer("id", "parameter_id")
    def serialize_ids(self, value: uuid.UUID) -> str:
        return str(value)


class LogEntryResponse(BaseModel):
    id: uuid.UUID
    action: SessionLogAction
    planned_exercise_id: uuid.UUID
    planned_exercise_name: str
    performed_exercise_id: uuid.UUID | None
    performed_exercise_name: str | None
    is_alternative: bool
    parameter_values: list[LogParameterValueResponse] = []

    @field_serializer("id", "planned_exercise_id", "performed_exercise_id")
    def serialize_ids(self, value: uuid.UUID | None) -> str | None:
        return str(value) if value is not None else None


class SessionLogResponse(BaseModel):
    id: uuid.UUID
    training_session_id: uuid.UUID
    performed_at: datetime
    note: str | None
    entries: list[LogEntryResponse] = []

    @field_serializer("id", "training_session_id")
    def serialize_ids(self, value: uuid.UUID) -> str:
        return str(value)


class SessionLogSummaryResponse(BaseModel):
    """List view of a log: the date + note, without its entries."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    performed_at: datetime
    note: str | None

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)
