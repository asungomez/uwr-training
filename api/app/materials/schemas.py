import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, computed_field, field_serializer

from app.models import MaterialCategory
from app.pagination import PaginationParams
from app.storage import MediaKind, public_url


class StartUploadRequest(BaseModel):
    """Begin a multipart upload. `kind` picks the constraints (a document or a
    recorded video) and the S3 folder."""

    kind: MediaKind
    content_type: str


class StartUploadResponse(BaseModel):
    """The S3 object key + multipart upload id, and the part size the client should
    slice the file into. The client uploads each part to its own presigned URL
    (`/materials/uploads/part`), then calls `/materials/uploads/complete`."""

    key: str
    upload_id: str
    part_size: int


class PartUrlRequest(BaseModel):
    key: str
    upload_id: str
    part_number: int


class PartUrlResponse(BaseModel):
    url: str


class FinishUploadRequest(BaseModel):
    """Complete or abort an in-progress multipart upload."""

    key: str
    upload_id: str


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
