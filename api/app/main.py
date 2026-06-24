from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import router as auth_router
from app.exercises import router as exercises_router
from app.health import router as health_router
from app.settings import settings
from app.trainings import router as trainings_router

app = FastAPI(title="uwr-training-api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(exercises_router)
app.include_router(trainings_router)
