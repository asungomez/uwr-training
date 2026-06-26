from collections.abc import Callable

import pytest
import sqlalchemy
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import StrengthTestItem


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
