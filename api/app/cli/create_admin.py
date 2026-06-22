"""`create-admin` command: create a new admin or promote an existing user."""

import argparse
import asyncio
import getpass
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models import User, UserRole
from app.security import hash_password
from app.settings import normalize_db_url

NAME = "create-admin"


def register(subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]") -> None:
    parser = subparsers.add_parser(NAME, help="Create or promote an admin user.")
    parser.add_argument("email")
    parser.add_argument(
        "--password",
        help="Admin password. Omit to be prompted securely (recommended).",
    )


def run(args: argparse.Namespace) -> None:
    password = args.password or _prompt_password()
    message = asyncio.run(_create_admin(normalize_db_url(args.database_url), args.email, password))
    print(message)


def _prompt_password() -> str:
    password = getpass.getpass("Password: ")
    if not password:
        sys.exit("Password must not be empty.")
    if password != getpass.getpass("Confirm password: "):
        sys.exit("Passwords do not match.")
    return password


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
