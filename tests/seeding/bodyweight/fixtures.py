from collections.abc import Callable

import pytest
import sqlalchemy
from sqlalchemy.orm import Session

from app.models import BodyweightLog
from seeding.bodyweight.factory import build_bodyweight_log


@pytest.fixture
def generate_bodyweight_log() -> Callable[..., BodyweightLog]:
    """Build an in-memory BodyweightLog (NOT persisted). Pass overrides for
    story-relevant fields, e.g. generate_bodyweight_log(weight_kg=80)."""
    return build_bodyweight_log


@pytest.fixture
def create_bodyweight_log(_db_engine: sqlalchemy.Engine) -> Callable[..., BodyweightLog]:
    """Build and persist a BodyweightLog, returning the detached instance.
    Pass athlete_id (and optionally recorded_at to control history order),
    e.g. create_bodyweight_log(athlete_id=member.id, weight_kg=80)."""

    def _create(**overrides: object) -> BodyweightLog:
        log = build_bodyweight_log(**overrides)
        with Session(_db_engine, expire_on_commit=False) as session:
            session.add(log)
            session.commit()
        return log

    return _create
