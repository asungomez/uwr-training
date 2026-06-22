from collections.abc import Callable
from urllib.parse import urlparse

import pytest
import sqlalchemy
from playwright.sync_api import Page
from sqlalchemy.orm import Session

from app.models import User
from app.security import SESSION_COOKIE, create_session_token
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


@pytest.fixture
def log_in_as(page: Page, app_url: str) -> Callable[[User], None]:
    """Authenticate by injecting the session cookie directly (no UI), so the
    arrange step is fast and not coupled to the login form working."""

    def _log_in(user: User) -> None:
        token = create_session_token(str(user.id))
        page.context.add_cookies(
            [
                {
                    "name": SESSION_COOKIE,
                    "value": token,
                    "domain": urlparse(app_url).hostname or "localhost",
                    "path": "/",
                    "httpOnly": True,
                    "sameSite": "Lax",
                }
            ]
        )

    return _log_in
