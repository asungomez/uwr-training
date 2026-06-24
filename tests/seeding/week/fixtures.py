from collections.abc import Callable

import pytest
import sqlalchemy
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Week
from seeding.week.factory import build_week


@pytest.fixture
def generate_week() -> Callable[..., Week]:
    """Build an in-memory Week (NOT persisted). Pass overrides for story-relevant
    fields, e.g. generate_week(phase="accumulation")."""
    return build_week


@pytest.fixture
def create_week(_db_engine: sqlalchemy.Engine) -> Callable[..., Week]:
    """Build and persist a Week, returning the detached instance. Position
    auto-appends across the calendar (unless overridden), so seeding several
    respects the unique position constraint. e.g. create_week(name="Semana 1")."""

    def _create(**overrides: object) -> Week:
        week = build_week(**overrides)
        with Session(_db_engine, expire_on_commit=False) as session:
            if "position" not in overrides:
                max_position = session.scalar(select(func.max(Week.position)))
                week.position = 0 if max_position is None else max_position + 1
            session.add(week)
            session.commit()
        return week

    return _create
