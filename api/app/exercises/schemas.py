import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, computed_field, field_serializer

from app.models import ExerciseType
from app.pagination import PaginationParams
from app.storage import MediaKind, public_url


class RelatedExerciseInput(BaseModel):
    related_exercise_id: uuid.UUID
    note: str | None = None


class ParameterInput(BaseModel):
    name: str
    description: str | None = None


class CreateExerciseRequest(BaseModel):
    name: str
    description: str | None = None
    type: ExerciseType
    thumbnail_key: str | None = None
    video_key: str | None = None
    related_exercises: list[RelatedExerciseInput] = []
    parameters: list[ParameterInput] = []


class UpdateExerciseRequest(BaseModel):
    name: str
    description: str | None = None
    type: ExerciseType
    thumbnail_key: str | None = None
    video_key: str | None = None
    related_exercises: list[RelatedExerciseInput] = []
    parameters: list[ParameterInput] = []


class ExerciseListParams(PaginationParams):
    """Query params for the exercises directory: pagination + filters."""

    search: str | None = None
    type: ExerciseType | None = None


class MediaUploadRequest(BaseModel):
    kind: MediaKind
    content_type: str


class MediaUploadResponse(BaseModel):
    """A presigned POST the client uses to upload one file directly to S3, plus
    the object key to store on the exercise once the upload succeeds."""

    key: str
    url: str
    fields: dict[str, str]


class RelatedExerciseResponse(BaseModel):
    """An alternative/related exercise as shown on the owning exercise: the target's
    id + name (to render and round-trip through the form), its thumbnail, plus the note."""

    related_exercise_id: uuid.UUID
    related_exercise_name: str
    related_exercise_thumbnail_url: str | None
    note: str | None

    @field_serializer("related_exercise_id")
    def serialize_related_id(self, value: uuid.UUID) -> str:
        return str(value)


class ParameterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)


class ExerciseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    type: ExerciseType
    created_at: datetime
    # Keys round-trip through the edit form; URLs (derived below) are for display.
    thumbnail_key: str | None = None
    video_key: str | None = None
    related_exercises: list[RelatedExerciseResponse] = []
    parameters: list[ParameterResponse] = []

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)

    @computed_field
    def thumbnail_url(self) -> str | None:
        return public_url(self.thumbnail_key)

    @computed_field
    def video_url(self) -> str | None:
        return public_url(self.video_key)
