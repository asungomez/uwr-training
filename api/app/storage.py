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


# Allowed content types and max upload size per media kind. Enforced both in the
# presigned POST conditions (server-side) and client-side before requesting one.
_THUMBNAIL_TYPES = {"image/jpeg", "image/png", "image/webp"}
_VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime"}

MEDIA_CONSTRAINTS: dict[MediaKind, tuple[set[str], int]] = {
    MediaKind.thumbnail: (_THUMBNAIL_TYPES, 5 * 1024 * 1024),  # 5 MB
    MediaKind.video: (_VIDEO_TYPES, 200 * 1024 * 1024),  # 200 MB
}

# File extension by content type, so stored keys keep a sensible suffix.
_EXTENSIONS = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "video/mp4": "mp4",
    "video/webm": "webm",
    "video/quicktime": "mov",
}


@lru_cache
def _client() -> "S3Client":
    """A boto3 S3 client. Cached; signs URLs locally (no network on presign)."""
    return boto3.client(
        "s3",
        region_name=settings.s3_region,
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
        endpoint_url=settings.s3_endpoint_url or None,
        config=Config(signature_version="s3v4"),
    )


def _new_key(kind: MediaKind, content_type: str) -> str:
    """An unguessable object key under the kind's folder, with a file extension."""
    ext = _EXTENSIONS.get(content_type, "bin")
    return f"exercises/{kind.value}/{uuid.uuid4().hex}.{ext}"


class PresignedUpload(NamedTuple):
    key: str
    url: str
    fields: dict[str, str]


def create_presigned_upload(kind: MediaKind, content_type: str) -> PresignedUpload:
    """Presigned POST for a direct browser→S3 upload. Returns the object key plus
    the {url, fields} the client posts the file with. Enforces content-type and a
    size ceiling via POST conditions."""
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
        ExpiresIn=300,
    )
    return PresignedUpload(key=key, url=presigned["url"], fields=presigned["fields"])


def public_url(key: str | None) -> str | None:
    """Public read URL for a stored object key, or None when there's no key."""
    if not key:
        return None
    base = settings.s3_public_base_url.rstrip("/")
    return f"{base}/{key}"
