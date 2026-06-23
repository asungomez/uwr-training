"""`migrate` command: bring the database up to head, skipping work when already current.

Run before the server starts (see render.yaml). A plain `alembic upgrade head` is
safe but pays a connection + version-check cost on every boot; on Render's free tier
(single instance, no rolling deploy) that lengthens restart downtime. This compares
the DB's applied revision against the script head and only upgrades on a mismatch, so
routine restarts (cold-start wake-ups, crashes) start the server immediately while a
genuine new migration still applies before traffic is served.
"""

import argparse
import asyncio
from pathlib import Path

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import command
from app.settings import normalize_db_url

NAME = "migrate"

# alembic.ini lives at the api project root (two levels up from app/cli/).
_ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"


def register(subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]") -> None:
    subparsers.add_parser(
        NAME,
        help="Upgrade the database to head, skipping the work when already current.",
    )


def run(args: argparse.Namespace) -> None:
    async_url = normalize_db_url(args.database_url)

    config = Config(str(_ALEMBIC_INI))
    config.set_main_option("sqlalchemy.url", async_url)

    head = ScriptDirectory.from_config(config).get_current_head()
    current = asyncio.run(_current_revision(async_url))

    if current == head:
        print(f"Database already at head ({head}); nothing to migrate.")
        return

    print(f"Migrating database: {current or 'base'} -> {head}…")
    command.upgrade(config, "head")
    print("Migration complete.")


async def _current_revision(async_url: str) -> str | None:
    """The revision currently stamped on the database, or None if unmigrated."""
    engine = create_async_engine(async_url)
    try:
        async with engine.connect() as connection:
            return await connection.run_sync(_revision_from_connection)
    finally:
        await engine.dispose()


def _revision_from_connection(connection: Connection) -> str | None:
    revision: str | None = MigrationContext.configure(connection).get_current_revision()
    return revision
