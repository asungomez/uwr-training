from collections.abc import Callable

import pytest
import sqlalchemy
from sqlalchemy.orm import Session

from app.models import Exercise
from seeding.exercise.factory import build_exercise

# A 1x1 PNG and a minimal MP4, so seeded media actually loads in the browser.
_PNG_1PX = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108020000009077"
    "53de0000000c4944415408d76360000002000154a24f5c0000000049454e44ae426082"
)


@pytest.fixture
def upload_media(_minio: tuple[object, str]) -> Callable[..., str]:
    """Put an object into the MinIO media bucket and return its key, so seeded
    exercises reference media that actually resolves. e.g.
    upload_media('thumbnail', 'image/png')."""
    import boto3

    _container, endpoint = _minio
    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
        region_name="us-east-1",
    )
    counter = {"n": 0}

    def _upload(kind: str = "thumbnail", content_type: str = "image/png") -> str:
        counter["n"] += 1
        ext = "png" if kind == "thumbnail" else "mp4"
        key = f"exercises/{kind}/test{counter['n']}.{ext}"
        s3.put_object(
            Bucket="uwr-media", Key=key, Body=_PNG_1PX, ContentType=content_type
        )
        return key

    return _upload


@pytest.fixture
def generate_exercise() -> Callable[..., Exercise]:
    """Build an in-memory Exercise (NOT persisted). Pass overrides for
    story-relevant fields, e.g. generate_exercise(name="Sentadilla")."""
    return build_exercise


@pytest.fixture
def create_exercise(_db_engine: sqlalchemy.Engine) -> Callable[..., Exercise]:
    """Build and persist an Exercise, returning the detached instance.
    e.g. create_exercise(name="Sentadilla", type="gym")."""

    def _create(**overrides: object) -> Exercise:
        exercise = build_exercise(**overrides)
        with Session(_db_engine, expire_on_commit=False) as session:
            session.add(exercise)
            session.commit()
        return exercise

    return _create
