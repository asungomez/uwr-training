"""S3 (or S3-compatible) storage for exercise media.

Uploads use a presigned POST so the browser sends bytes straight to S3 — they
never pass through the API. We store only the object key in the DB and build
public read URLs at serialization time.
"""

import enum
import uuid
from functools import lru_cache
from typing import TYPE_CHECKING, NamedTuple

import boto3
from botocore.client import Config

from app.settings import settings

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client


class MediaKind(enum.StrEnum):
    thumbnail = "thumbnail"
    video = "video"
    # Support materials (admin-uploaded). Documents cover PDFs/office files; videos
    # are recorded sessions (laxer/larger than exercise demo clips).
    material_document = "material_document"
    material_video = "material_video"


# Allowed content types and max upload size per media kind. Enforced both in the
# presigned POST conditions (server-side) and client-side before requesting one.
_THUMBNAIL_TYPES = {"image/jpeg", "image/png", "image/webp"}
_VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime"}
_DOCUMENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # .pptx
    "text/plain",
    "text/csv",
}

MEDIA_CONSTRAINTS: dict[MediaKind, tuple[set[str], int]] = {
    MediaKind.thumbnail: (_THUMBNAIL_TYPES, 5 * 1024 * 1024),  # 5 MB
    MediaKind.video: (_VIDEO_TYPES, 200 * 1024 * 1024),  # 200 MB
    MediaKind.material_document: (_DOCUMENT_TYPES, 50 * 1024 * 1024),  # 50 MB
    MediaKind.material_video: (_VIDEO_TYPES, 500 * 1024 * 1024),  # 500 MB
}

# File extension by content type, so stored keys keep a sensible suffix.
_EXTENSIONS = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "video/mp4": "mp4",
    "video/webm": "webm",
    "video/quicktime": "mov",
    "application/pdf": "pdf",
    "application/msword": "doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.ms-excel": "xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "application/vnd.ms-powerpoint": "ppt",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
    "text/plain": "txt",
    "text/csv": "csv",
}

# Which top-level folder each media kind's objects live under.
_KEY_PREFIX = {
    MediaKind.thumbnail: "exercises/thumbnail",
    MediaKind.video: "exercises/video",
    MediaKind.material_document: "materials/document",
    MediaKind.material_video: "materials/video",
}


@lru_cache
def _client() -> "S3Client":
    """A boto3 S3 client. Cached; signs URLs locally (no network on presign).

    With no custom endpoint (real AWS), pin the regional endpoint explicitly. The
    default global endpoint (s3.amazonaws.com) 307-redirects to the bucket's region
    for non-us-east-1 buckets, and that redirect lacks CORS headers — so a browser
    upload to it fails as a (misleading) "CORS" error. Addressing the region
    directly avoids the redirect entirely.
    """
    endpoint_url = settings.s3_endpoint_url or f"https://s3.{settings.s3_region}.amazonaws.com"
    return boto3.client(
        "s3",
        region_name=settings.s3_region,
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
        endpoint_url=endpoint_url,
        config=Config(signature_version="s3v4"),
    )


def _new_key(kind: MediaKind, content_type: str) -> str:
    """An unguessable object key under the kind's folder, with a file extension."""
    ext = _EXTENSIONS.get(content_type, "bin")
    return f"{_KEY_PREFIX[kind]}/{uuid.uuid4().hex}.{ext}"


class PresignedUpload(NamedTuple):
    key: str
    url: str
    fields: dict[str, str]


def create_presigned_upload(kind: MediaKind, content_type: str) -> PresignedUpload:
    """Presigned POST for a direct browser→S3 upload. Returns the object key plus
    the {url, fields} the client posts the file with. Enforces content-type and a
    size ceiling via POST conditions. The URL stays valid for 2h so large uploads
    (e.g. a 1h session video on a slow connection) don't expire mid-transfer."""
    _allowed_types, max_size = MEDIA_CONSTRAINTS[kind]
    key = _new_key(kind, content_type)
    presigned = _client().generate_presigned_post(
        Bucket=settings.s3_bucket,
        Key=key,
        Fields={"Content-Type": content_type},
        Conditions=[
            {"Content-Type": content_type},
            ["content-length-range", 1, max_size],
        ],
        ExpiresIn=2 * 60 * 60,  # 2 hours
    )
    return PresignedUpload(key=key, url=presigned["url"], fields=presigned["fields"])


def public_url(key: str | None) -> str | None:
    """Public read URL for a stored object key, or None when there's no key."""
    if not key:
        return None
    base = settings.s3_public_base_url.rstrip("/")
    return f"{base}/{key}"
