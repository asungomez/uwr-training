import os
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.settings import settings

# On AWS Lambda each execution is a short-lived, frozen-between-invocations process, and
# a pooled async connection can't safely persist across invocations (it gets bound to
# one invocation's event loop, and idle pooled connections would also count against
# RDS's small max_connections). So on Lambda we use NullPool: a fresh connection per
# session, closed when the session context exits. Everywhere else keeps the pool.
if "AWS_LAMBDA_FUNCTION_NAME" in os.environ:
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
else:
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
