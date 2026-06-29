import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, computed_field, field_serializer

from app.models import MaterialCategory
from app.pagination import PaginationParams
from app.storage import MediaKind, public_url


class MaterialUploadRequest(BaseModel):
    """Ask for a presigned upload. `kind` picks the constraints (a document or a
    recorded video) and the S3 folder."""

    kind: MediaKind
    content_type: str


class MaterialUploadResponse(BaseModel):
    """A presigned POST the client uses to upload one file directly to S3, plus the
    object key to store on the material once the upload succeeds."""

    key: str
    url: str
    fields: dict[str, str]


class CreateMaterialRequest(BaseModel):
    title: str
    category: MaterialCategory
    file_key: str


class UpdateMaterialRequest(BaseModel):
    title: str
    category: MaterialCategory
    file_key: str


class MaterialListParams(PaginationParams):
    """Query params for the materials list: pagination + optional category filter."""

    category: MaterialCategory | None = None
    search: str | None = None


class MaterialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    category: MaterialCategory
    # The key round-trips through the edit form; the URL (derived) is for access.
    file_key: str
    created_at: datetime

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)

    @computed_field
    def file_url(self) -> str | None:
        return public_url(self.file_key)
