import uuid
from collections.abc import Callable

import pytest
import sqlalchemy
from sqlalchemy.orm import Session

from app.models import (
    LacticAcidPersonalBestLog,
    LacticAcidTestResultLog,
    LacticAcidTestWarmup,
)


@pytest.fixture
def create_lactic_acid_test_warmup(
    _db_engine: sqlalchemy.Engine,
) -> Callable[..., LacticAcidTestWarmup]:
    """Point the singleton lactic-acid-test warmup at an existing pool TrainingSession.
    e.g. create_lactic_acid_test_warmup(training_session_id=warmup.id)."""

    def _create(*, training_session_id: uuid.UUID) -> LacticAcidTestWarmup:
        with Session(_db_engine, expire_on_commit=False) as session:
            pointer = LacticAcidTestWarmup(training_session_id=training_session_id)
            session.add(pointer)
            session.commit()
        return pointer

    return _create


@pytest.fixture
def create_lactic_acid_personal_best_log(
    _db_engine: sqlalchemy.Engine,
) -> Callable[..., LacticAcidPersonalBestLog]:
    """Persist a lactic-acid personal-best log. e.g.
    create_lactic_acid_personal_best_log(athlete_id=u.id, seconds=40.5, week_id=w.id)."""

    def _create(**overrides: object) -> LacticAcidPersonalBestLog:
        with Session(_db_engine, expire_on_commit=False) as session:
            log = LacticAcidPersonalBestLog(**overrides)
            session.add(log)
            session.commit()
        return log

    return _create


@pytest.fixture
def create_lactic_acid_test_result_log(
    _db_engine: sqlalchemy.Engine,
) -> Callable[..., LacticAcidTestResultLog]:
    """Persist a lactic-acid test-result log. e.g.
    create_lactic_acid_test_result_log(athlete_id=u.id, seconds=44.5, week_id=w.id)."""

    def _create(**overrides: object) -> LacticAcidTestResultLog:
        with Session(_db_engine, expire_on_commit=False) as session:
            log = LacticAcidTestResultLog(**overrides)
            session.add(log)
            session.commit()
        return log

    return _create
