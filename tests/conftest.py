"""E2E test harness.

Spins up db + api + frontend as throwaway containers on a private Docker network,
with random host ports (so a running dev stack on 5173/8000/5432 is untouched).
Migrations run once per session; every table is truncated before each test.
"""

import os
from collections.abc import Iterator
from pathlib import Path

# The session-cookie JWT is signed host-side (log_in_as) and verified in the api
# container, so both must share SECRET_KEY. Set it before any `app.*` import so
# app.settings picks it up.
SECRET_KEY = "test-secret-key-at-least-32-bytes-long"
os.environ["SECRET_KEY"] = SECRET_KEY

import pytest
import sqlalchemy
from sqlalchemy import text
from testcontainers.core.container import DockerContainer
from testcontainers.core.network import Network
from testcontainers.core.waiting_utils import wait_for_logs

# Seeding fixtures (generate_user, create_user, log_in_as, …) live in dedicated modules.
pytest_plugins = ["seeding.user.fixtures", "seeding.exercise.fixtures"]

REPO_ROOT = Path(__file__).resolve().parent.parent

DB_USER = "uwr"
DB_PASSWORD = "uwr"
DB_NAME = "uwr"
# Internal (container-network) URL the api uses to reach the db.
INTERNAL_DB_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@db:5432/{DB_NAME}"


def _build_image(tag: str, dockerfile: str) -> None:
    """Build an image from a repo Dockerfile with the repo root as context."""
    import docker

    client = docker.from_env()
    client.images.build(
        path=str(REPO_ROOT),
        dockerfile=dockerfile,
        tag=tag,
        rm=True,
    )


@pytest.fixture(scope="session")
def _network() -> Iterator[Network]:
    with Network() as network:
        yield network


@pytest.fixture(scope="session")
def _db(_network: Network) -> Iterator[DockerContainer]:
    container = (
        DockerContainer("postgres:16")
        .with_env("POSTGRES_USER", DB_USER)
        .with_env("POSTGRES_PASSWORD", DB_PASSWORD)
        .with_env("POSTGRES_DB", DB_NAME)
        .with_exposed_ports(5432)
        .with_network(_network)
        .with_network_aliases("db")
    )
    with container:
        wait_for_logs(
            container,
            "database system is ready to accept connections",
            timeout=30,
        )
        yield container


@pytest.fixture(scope="session")
def _api(_network: Network, _db: DockerContainer) -> Iterator[DockerContainer]:
    _build_image("uwr-training-api:test", "docker/dockerfiles/api.Dockerfile")
    container = (
        DockerContainer("uwr-training-api:test")
        .with_env("DATABASE_URL", INTERNAL_DB_URL)
        .with_env("SECRET_KEY", SECRET_KEY)
        .with_env("COOKIE_SECURE", "false")
        .with_exposed_ports(8000)
        .with_network(_network)
        .with_network_aliases("api")
    )
    with container:
        wait_for_logs(container, "Application startup complete", timeout=60)
        # Apply migrations inside the api container (same path as deploy).
        code, output = container.exec(["uv", "run", "alembic", "upgrade", "head"])
        if code != 0:
            raise RuntimeError(f"alembic upgrade failed:\n{output.decode()}")
        yield container


@pytest.fixture(scope="session")
def _frontend(_network: Network, _api: DockerContainer) -> Iterator[DockerContainer]:
    _build_image("uwr-training-frontend:test", "docker/dockerfiles/frontend.Dockerfile")
    container = (
        DockerContainer("uwr-training-frontend:test")
        # Vite dev proxy forwards /api to the api container over the private network.
        .with_env("API_PROXY_TARGET", "http://api:8000")
        .with_exposed_ports(5173)
        .with_network(_network)
        .with_network_aliases("frontend")
    )
    with container:
        wait_for_logs(container, "VITE", timeout=60)
        yield container


@pytest.fixture(scope="session")
def _db_engine(_db: DockerContainer) -> Iterator[sqlalchemy.Engine]:
    """A host-side sync engine (psycopg2) for truncating between tests."""
    host = _db.get_container_host_ip()
    port = _db.get_exposed_port(5432)
    engine = sqlalchemy.create_engine(
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{host}:{port}/{DB_NAME}"
    )
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def app_url(_frontend: DockerContainer) -> str:
    """Frontend URL on its random host port (kept off the dev stack's 5173)."""
    host = _frontend.get_container_host_ip()
    port = _frontend.get_exposed_port(5173)
    return f"http://{host}:{port}"


@pytest.fixture(autouse=True)
def _clean_db(_api: DockerContainer, _db_engine: sqlalchemy.Engine) -> None:
    """Empty every table before each test (schema/migrations intact)."""
    with _db_engine.begin() as conn:
        tables = conn.execute(
            text(
                "SELECT tablename FROM pg_tables "
                "WHERE schemaname = 'public' AND tablename <> 'alembic_version'"
            )
        ).scalars().all()
        if tables:
            joined = ", ".join(f'"{t}"' for t in tables)
            conn.execute(text(f"TRUNCATE {joined} RESTART IDENTITY CASCADE"))
