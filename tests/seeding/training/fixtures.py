from collections.abc import Callable

import pytest
import sqlalchemy
from sqlalchemy import func, select
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
    Position auto-appends within its category+subtype (unless overridden), so
    seeding several in the same scope respects the unique (cat, subtype, position)
    constraint. e.g. create_training(title="Fuerza", category="gym")."""

    def _create(**overrides: object) -> TrainingSession:
        training = build_training(**overrides)
        with Session(_db_engine, expire_on_commit=False) as session:
            if "position" not in overrides:
                max_position = session.scalar(
                    select(func.max(TrainingSession.position)).where(
                        TrainingSession.category == training.category,
                        TrainingSession.subtype == training.subtype,
                    )
                )
                training.position = 0 if max_position is None else max_position + 1
            session.add(training)
            session.commit()
        return training

    return _create
