import uuid

from pydantic import BaseModel, field_serializer


class StrengthTestItemInput(BaseModel):
    """One row of the strength test as submitted by the admin: a gym exercise and
    the multiplier applied to body weight for the target load."""

    exercise_id: uuid.UUID
    weight_multiplier: float


class UpdateStrengthTestRequest(BaseModel):
    """Replaces the whole strength test with this ordered list of items."""

    items: list[StrengthTestItemInput] = []


class StrengthTestItemResponse(BaseModel):
    id: uuid.UUID
    exercise_id: uuid.UUID
    exercise_name: str
    weight_multiplier: float

    @field_serializer("id", "exercise_id")
    def serialize_ids(self, value: uuid.UUID) -> str:
        return str(value)


class StrengthTestResponse(BaseModel):
    """The strength test: its ordered exercises with their multipliers."""

    items: list[StrengthTestItemResponse] = []
