"""Admin CLI. Run via `make admin command='...'`.

Connects to the database in DATABASE_URL by default, or to --database-url if given
(use Render's external connection string to manage the deployed DB from your laptop).
"""

import argparse
import asyncio
import getpass
import os
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import DEFAULT_DATABASE_URL, normalize_db_url
from app.models import User, UserRole
from app.security import hash_password


async def _create_admin(database_url: str, email: str, password: str) -> str:
    email = email.strip().lower()
    engine = create_async_engine(database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as session:
            existing = await session.scalar(select(User).where(User.email == email))
            if existing is not None:
                existing.hashed_password = hash_password(password)
                existing.role = UserRole.admin
                existing.is_active = True
                await session.commit()
                return f"Updated existing user {email} to active admin."
            session.add(
                User(
                    email=email,
                    hashed_password=hash_password(password),
                    role=UserRole.admin,
                )
            )
            await session.commit()
            return f"Created admin {email}."
    finally:
        await engine.dispose()


def _prompt_password() -> str:
    password = getpass.getpass("Password: ")
    if not password:
        sys.exit("Password must not be empty.")
    if password != getpass.getpass("Confirm password: "):
        sys.exit("Passwords do not match.")
    return password


def main() -> None:
    parser = argparse.ArgumentParser(prog="app.cli", description="Admin CLI")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL),
        help="Override the target database (e.g. Render's external connection string).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create-admin", help="Create or promote an admin user.")
    create.add_argument("email")
    create.add_argument(
        "--password",
        help="Admin password. Omit to be prompted securely (recommended).",
    )

    args = parser.parse_args()

    if args.command == "create-admin":
        password = args.password or _prompt_password()
        message = asyncio.run(
            _create_admin(normalize_db_url(args.database_url), args.email, password)
        )
        print(message)


if __name__ == "__main__":
    main()
