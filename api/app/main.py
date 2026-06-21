import os
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import router as auth_router
from app.db import get_session

app = FastAPI(title="uwr-training-api")

# Comma-separated list of allowed front-end origins; defaults to the local dev server.
cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins if origin.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


class HealthResponse(BaseModel):
    status: str


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello, world"}


@app.get("/health")
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/db-health")
async def db_health(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> HealthResponse:
    await session.execute(text("SELECT 1"))
    return HealthResponse(status="ok")
