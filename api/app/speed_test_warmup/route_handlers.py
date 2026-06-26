from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import current_user, require_admin
from app.db import get_session
from app.models import SpeedTestWarmup, TrainingCategory, TrainingSession, TrainingSubtype, User
from app.trainings.route_handlers import _build_blocks, _load_with_blocks, _validate_exercises
from app.trainings.schemas import TrainingSessionDetailResponse, UpdateTrainingRequest

router = APIRouter(prefix="/speed-test/warmup", tags=["speed-test-warmup"])

# The warmup lives as a pool TrainingSession. Its subtype is arbitrary (it never
# appears in the pool list or counts towards a week), so pick a valid pool one.
_WARMUP_CATEGORY = TrainingCategory.pool
_WARMUP_SUBTYPE = TrainingSubtype.endurance


async def _get_or_create_warmup_session(session: AsyncSession) -> TrainingSession:
    """The pool TrainingSession backing the speed-test warmup, created empty on first
    access so the singleton always exists. Position -1 keeps it out of the normal
    scope's 0..n ordering."""
    pointer = await session.scalar(select(SpeedTestWarmup))
    if pointer is not None:
        training = await _load_with_blocks(session, pointer.training_session_id)
        assert training is not None
        return training

    training = TrainingSession(
        category=_WARMUP_CATEGORY,
        subtype=_WARMUP_SUBTYPE,
        position=-1,
        title="Calentamiento prueba de velocidad",
    )
    session.add(training)
    await session.flush()
    session.add(SpeedTestWarmup(training_session_id=training.id))
    await session.commit()

    reloaded = await _load_with_blocks(session, training.id)
    assert reloaded is not None
    return reloaded


@router.get("", response_model=TrainingSessionDetailResponse)
async def get_warmup(
    _user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TrainingSession:
    """The speed-test warmup session (with its blocks). Visible to any user."""
    return await _get_or_create_warmup_session(session)


@router.put("", response_model=TrainingSessionDetailResponse)
async def update_warmup(
    body: UpdateTrainingRequest,
    _admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TrainingSession:
    """Replace the warmup's title and block tree. Same shape as editing any training
    session — it IS a pool session — but fixed to the singleton warmup."""
    training = await _get_or_create_warmup_session(session)
    await _validate_exercises(session, body.blocks)

    title = body.title.strip() if body.title else None
    training.title = title or None
    training.blocks = _build_blocks(body.blocks)
    await session.commit()

    reloaded = await _load_with_blocks(session, training.id)
    assert reloaded is not None
    return reloaded
