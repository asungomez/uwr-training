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
    MaterialListParams,
    MaterialResponse,
    MaterialUploadRequest,
    MaterialUploadResponse,
    UpdateMaterialRequest,
)
from app.models import Material, User
from app.pagination import Page
from app.storage import MEDIA_CONSTRAINTS, MediaKind, create_presigned_upload

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


@router.post("/media-uploads", response_model=MaterialUploadResponse)
async def create_material_upload(
    body: MaterialUploadRequest,
    _admin: Annotated[User, Depends(require_admin)],
) -> MaterialUploadResponse:
    """Mint a presigned POST so the admin's browser uploads a material file straight
    to S3. Returns the object key to store on save."""
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
    upload = create_presigned_upload(body.kind, body.content_type)
    return MaterialUploadResponse(key=upload.key, url=upload.url, fields=upload.fields)


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
