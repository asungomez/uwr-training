import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import current_user, require_admin
from app.db import get_session
from app.errors import ErrorCode, api_error
from app.materials.schemas import (
    CreateMaterialRequest,
    FinishUploadRequest,
    MaterialListParams,
    MaterialResponse,
    PartUrlRequest,
    PartUrlResponse,
    StartUploadRequest,
    StartUploadResponse,
    UpdateMaterialRequest,
)
from app.models import Material, User
from app.pagination import Page
from app.storage import (
    MEDIA_CONSTRAINTS,
    MULTIPART_PART_SIZE,
    MediaKind,
    abort_multipart_upload,
    complete_multipart_upload,
    create_multipart_upload,
    presign_part,
)

router = APIRouter(prefix="/materials", tags=["materials"])

# Only these media kinds belong to materials (not exercise thumbnails/clips).
_MATERIAL_KINDS = {MediaKind.material_document, MediaKind.material_video}


def _validate(title: str, file_key: str) -> str:
    """Validate a material's submitted fields, returning the trimmed title."""
    trimmed = title.strip()
    if not trimmed:
        raise api_error(
            status.HTTP_400_BAD_REQUEST, ErrorCode.invalid_material, "Title is required"
        )
    if not file_key.strip():
        raise api_error(
            status.HTTP_400_BAD_REQUEST, ErrorCode.invalid_material, "A file is required"
        )
    return trimmed


@router.post("/uploads/start", response_model=StartUploadResponse)
async def start_upload(
    body: StartUploadRequest,
    _admin: Annotated[User, Depends(require_admin)],
) -> StartUploadResponse:
    """Begin a multipart upload for a material file. The browser then PUTs each part
    to its own presigned URL and finishes with /uploads/complete. Multipart lets the
    progress bar track bytes S3 actually accepts (not just flushed to a socket)."""
    if body.kind not in _MATERIAL_KINDS:
        raise api_error(
            status.HTTP_400_BAD_REQUEST, ErrorCode.invalid_material, "Invalid material kind"
        )
    allowed_types, _max_size = MEDIA_CONSTRAINTS[body.kind]
    if body.content_type not in allowed_types:
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            ErrorCode.invalid_media_type,
            f"Unsupported content type for {body.kind.value}",
        )
    upload = create_multipart_upload(body.kind, body.content_type)
    return StartUploadResponse(
        key=upload.key, upload_id=upload.upload_id, part_size=MULTIPART_PART_SIZE
    )


@router.post("/uploads/part", response_model=PartUrlResponse)
async def upload_part_url(
    body: PartUrlRequest,
    _admin: Annotated[User, Depends(require_admin)],
) -> PartUrlResponse:
    """A presigned PUT URL for one part of an in-progress multipart upload."""
    return PartUrlResponse(url=presign_part(body.key, body.upload_id, body.part_number))


@router.post("/uploads/complete", status_code=status.HTTP_204_NO_CONTENT)
async def complete_upload(
    body: FinishUploadRequest,
    _admin: Annotated[User, Depends(require_admin)],
) -> None:
    """Finalize a multipart upload into a single object (reads the parts S3 recorded)."""
    complete_multipart_upload(body.key, body.upload_id)


@router.post("/uploads/abort", status_code=status.HTTP_204_NO_CONTENT)
async def abort_upload(
    body: FinishUploadRequest,
    _admin: Annotated[User, Depends(require_admin)],
) -> None:
    """Discard an in-progress multipart upload (on cancel or failure)."""
    abort_multipart_upload(body.key, body.upload_id)


@router.get("", response_model=Page[MaterialResponse])
async def list_materials(
    _user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    params: Annotated[MaterialListParams, Query()],
) -> Page[MaterialResponse]:
    """All materials, filterable by category and title search, most recent first.
    Visible to any authenticated user."""
    filters: list[ColumnElement[bool]] = []
    if params.category is not None:
        filters.append(Material.category == params.category)
    if params.search:
        filters.append(Material.title.ilike(f"%{params.search.strip()}%"))

    total = await session.scalar(select(func.count()).select_from(Material).where(*filters))
    rows = await session.scalars(
        select(Material)
        .where(*filters)
        .order_by(Material.created_at.desc())
        .offset(params.offset)
        .limit(params.page_size)
    )
    return Page(
        items=[MaterialResponse.model_validate(row) for row in rows.all()],
        total_count=total or 0,
    )


@router.get("/{material_id}", response_model=MaterialResponse)
async def get_material(
    material_id: uuid.UUID,
    _user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Material:
    """A single material by id. Visible to any authenticated user."""
    material = await session.get(Material, material_id)
    if material is None:
        raise api_error(
            status.HTTP_404_NOT_FOUND, ErrorCode.material_not_found, "Material not found"
        )
    return material


@router.post("", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
async def create_material(
    body: CreateMaterialRequest,
    _admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Material:
    """Create a material (admin only). The file must already be uploaded to S3 via
    the presigned-upload endpoint; `file_key` is the key returned there."""
    title = _validate(body.title, body.file_key)
    material = Material(title=title, category=body.category, file_key=body.file_key)
    session.add(material)
    await session.commit()
    await session.refresh(material)
    return material


@router.put("/{material_id}", response_model=MaterialResponse)
async def update_material(
    material_id: uuid.UUID,
    body: UpdateMaterialRequest,
    _admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Material:
    """Update a material (admin only)."""
    material = await session.get(Material, material_id)
    if material is None:
        raise api_error(
            status.HTTP_404_NOT_FOUND, ErrorCode.material_not_found, "Material not found"
        )

    material.title = _validate(body.title, body.file_key)
    material.category = body.category
    material.file_key = body.file_key
    await session.commit()
    await session.refresh(material)
    return material


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_material(
    material_id: uuid.UUID,
    _admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Delete a material (admin only)."""
    material = await session.get(Material, material_id)
    if material is None:
        raise api_error(
            status.HTTP_404_NOT_FOUND, ErrorCode.material_not_found, "Material not found"
        )
    await session.delete(material)
    await session.commit()
