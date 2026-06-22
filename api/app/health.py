from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str


@router.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello, world"}


@router.get("/health")
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/db-health")
async def db_health(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> HealthResponse:
    await session.execute(text("SELECT 1"))
    return HealthResponse(status="ok")
