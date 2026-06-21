import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="uwr-training-api")

# Comma-separated list of allowed front-end origins; defaults to the local dev server.
cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins if origin.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello, world"}


@app.get("/health")
async def health() -> HealthResponse:
    return HealthResponse(status="ok")
