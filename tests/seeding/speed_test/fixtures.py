import uuid
from collections.abc import Callable

import pytest
import sqlalchemy
from sqlalchemy.orm import Session

from app.models import SpeedTestLog, SpeedTestWarmup


@pytest.fixture
def create_speed_test_warmup(_db_engine: sqlalchemy.Engine) -> Callable[..., SpeedTestWarmup]:
    """Point the singleton speed-test warmup at an existing pool TrainingSession.
    e.g. create_speed_test_warmup(training_session_id=warmup.id)."""

    def _create(*, training_session_id: uuid.UUID) -> SpeedTestWarmup:
        with Session(_db_engine, expire_on_commit=False) as session:
            pointer = SpeedTestWarmup(training_session_id=training_session_id)
            session.add(pointer)
            session.commit()
        return pointer

    return _create


@pytest.fixture
def create_speed_test_log(_db_engine: sqlalchemy.Engine) -> Callable[..., SpeedTestLog]:
    """Persist a speed-test log for an athlete. e.g.
    create_speed_test_log(athlete_id=u.id, seconds=11.5, week_id=w.id)."""

    def _create(**overrides: object) -> SpeedTestLog:
        with Session(_db_engine, expire_on_commit=False) as session:
            log = SpeedTestLog(**overrides)
            session.add(log)
            session.commit()
        return log

    return _create
