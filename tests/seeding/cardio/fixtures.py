from collections.abc import Callable

import pytest
import sqlalchemy
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import CardioTraining
from seeding.cardio.factory import build_cardio_training


@pytest.fixture
def generate_cardio_training() -> Callable[..., CardioTraining]:
    """Build an in-memory CardioTraining (NOT persisted). Pass overrides for
    story-relevant fields, e.g. generate_cardio_training(subtype="anaerobic")."""
    return build_cardio_training


@pytest.fixture
def create_cardio_training(_db_engine: sqlalchemy.Engine) -> Callable[..., CardioTraining]:
    """Build and persist a CardioTraining, returning the detached instance.
    Position auto-appends within its subtype (unless overridden), so seeding
    several in the same subtype respects the unique (subtype, position)
    constraint. e.g. create_cardio_training(title="Series", subtype="aerobic")."""

    def _create(**overrides: object) -> CardioTraining:
        training = build_cardio_training(**overrides)
        with Session(_db_engine, expire_on_commit=False) as session:
            if "position" not in overrides:
                max_position = session.scalar(
                    select(func.max(CardioTraining.position)).where(
                        CardioTraining.subtype == training.subtype,
                    )
                )
                training.position = 0 if max_position is None else max_position + 1
            session.add(training)
            session.commit()
        return training

    return _create
