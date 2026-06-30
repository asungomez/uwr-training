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


class GymMaterialInput(BaseModel):
    """A material on the exercise form — just its name. The server finds an existing
    material by name (case-insensitive) or creates one, then links it."""

    name: str


class GymFacilityInput(BaseModel):
    """A facility on the exercise form — just its name. The server finds an existing
    facility by name (case-insensitive) or creates one, then links it."""

    name: str


class CreateExerciseRequest(BaseModel):
    name: str
    description: str | None = None
    type: ExerciseType
    thumbnail_key: str | None = None
    video_key: str | None = None
    related_exercises: list[RelatedExerciseInput] = []
    parameters: list[ParameterInput] = []
    gym_materials: list[GymMaterialInput] = []
    gym_facilities: list[GymFacilityInput] = []


class UpdateExerciseRequest(BaseModel):
    name: str
    description: str | None = None
    type: ExerciseType
    thumbnail_key: str | None = None
    video_key: str | None = None
    related_exercises: list[RelatedExerciseInput] = []
    parameters: list[ParameterInput] = []
    gym_materials: list[GymMaterialInput] = []
    gym_facilities: list[GymFacilityInput] = []


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


class GymMaterialResponse(BaseModel):
    """A gym material as shown on an exercise (and in the autocomplete suggestions)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)


class GymMaterialListParams(PaginationParams):
    """Query params for the gym-materials autocomplete: pagination + name search."""

    search: str | None = None


class GymFacilityResponse(BaseModel):
    """A gym facility as shown on an exercise (and in the autocomplete suggestions)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)


class GymFacilityListParams(PaginationParams):
    """Query params for the gym-facilities autocomplete: pagination + name search."""

    search: str | None = None


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
    gym_materials: list[GymMaterialResponse] = []
    gym_facilities: list[GymFacilityResponse] = []

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)

    @computed_field
    def thumbnail_url(self) -> str | None:
        return public_url(self.thumbnail_key)

    @computed_field
    def video_url(self) -> str | None:
        return public_url(self.video_key)


class ExerciseLogParameterValue(BaseModel):
    """One parameter value recorded for an exercise on a past session."""

    name: str
    value: str


class ExerciseLogEntry(BaseModel):
    """One past occurrence of the athlete doing this exercise: when, in which
    training, whether it stood in as an alternative, and the values recorded."""

    log_id: uuid.UUID
    training_id: uuid.UUID
    training_title: str | None
    performed_at: datetime
    # Set when this exercise was performed as an alternative to a different planned one.
    as_alternative_for: str | None
    parameter_values: list[ExerciseLogParameterValue] = []

    @field_serializer("log_id", "training_id")
    def serialize_ids(self, value: uuid.UUID) -> str:
        return str(value)
