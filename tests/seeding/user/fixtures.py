from collections.abc import Callable

import pytest
import sqlalchemy
from sqlalchemy.orm import Session

from app.models import User
from seeding.user.factory import build_user


@pytest.fixture
def generate_user() -> Callable[..., User]:
    """Build an in-memory User (NOT persisted). Pass overrides for story-relevant
    fields, e.g. generate_user(role="admin")."""
    return build_user


@pytest.fixture
def create_user(_db_engine: sqlalchemy.Engine) -> Callable[..., User]:
    """Build and persist a User, returning the detached instance.
    e.g. create_user(role="admin")."""

    def _create(**overrides: object) -> User:
        user = build_user(**overrides)
        with Session(_db_engine, expire_on_commit=False) as session:
            session.add(user)
            session.commit()
        return user

    return _create
