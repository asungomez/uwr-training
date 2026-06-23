from collections.abc import Callable

import pytest
import sqlalchemy
from sqlalchemy.orm import Session

from app.models import Exercise
from seeding.exercise.factory import build_exercise


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
