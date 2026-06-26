import uuid
from collections.abc import Callable

import pytest
import sqlalchemy
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import StrengthTestItem, StrengthTestLog, StrengthTestLogEntry


@pytest.fixture
def create_strength_test_item(_db_engine: sqlalchemy.Engine) -> Callable[..., StrengthTestItem]:
    """Build and persist one strength-test item, returning the detached instance.
    Position auto-appends unless overridden. e.g.
    create_strength_test_item(exercise_id=ex.id, weight_multiplier=1.5)."""

    def _create(**overrides: object) -> StrengthTestItem:
        with Session(_db_engine, expire_on_commit=False) as session:
            if "position" not in overrides:
                max_position = session.scalar(select(func.max(StrengthTestItem.position)))
                overrides["position"] = 0 if max_position is None else max_position + 1
            item = StrengthTestItem(**overrides)
            session.add(item)
            session.commit()
        return item

    return _create


@pytest.fixture
def create_strength_test_log(
    _db_engine: sqlalchemy.Engine,
) -> Callable[..., StrengthTestLog]:
    """Persist a strength-test log for an athlete with a result per exercise. Pass
    athlete_id, bodyweight_kg, and results as {exercise_id: actual_weight_kg}. e.g.
    create_strength_test_log(athlete_id=u.id, bodyweight_kg=80, results={ex.id: 100})."""

    def _create(
        *,
        athlete_id: uuid.UUID,
        bodyweight_kg: float = 80.0,
        results: dict[uuid.UUID, float] | None = None,
        **overrides: object,
    ) -> StrengthTestLog:
        with Session(_db_engine, expire_on_commit=False) as session:
            log = StrengthTestLog(
                athlete_id=athlete_id, bodyweight_kg=bodyweight_kg, **overrides
            )
            for position, (exercise_id, actual) in enumerate((results or {}).items()):
                log.entries.append(
                    StrengthTestLogEntry(
                        position=position,
                        exercise_id=exercise_id,
                        target_weight_kg=actual,
                        actual_weight_kg=actual,
                    )
                )
            session.add(log)
            session.commit()
        return log

    return _create
