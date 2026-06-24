from collections.abc import Callable

import pytest
import sqlalchemy
from sqlalchemy.orm import Session

from app.models import TrainingSession
from seeding.training.factory import build_training


@pytest.fixture
def generate_training() -> Callable[..., TrainingSession]:
    """Build an in-memory TrainingSession (NOT persisted). Pass overrides for
    story-relevant fields, e.g. generate_training(category="pool")."""
    return build_training


@pytest.fixture
def create_training(_db_engine: sqlalchemy.Engine) -> Callable[..., TrainingSession]:
    """Build and persist a TrainingSession, returning the detached instance.
    e.g. create_training(title="Fuerza", category="gym", subtype="accumulation")."""

    def _create(**overrides: object) -> TrainingSession:
        training = build_training(**overrides)
        with Session(_db_engine, expire_on_commit=False) as session:
            session.add(training)
            session.commit()
        return training

    return _create
