from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import current_user
from app.bodyweight_logs.schemas import (
    BodyweightLogResponse,
    CreateBodyweightLogRequest,
)
from app.db import get_session
from app.errors import ErrorCode, api_error
from app.models import BodyweightLog, User
from app.pagination import Page, PaginationParams

# The number of most-recent points the history graph plots.
GRAPH_POINTS = 10

router = APIRouter(prefix="/bodyweight-logs", tags=["bodyweight-logs"])


@router.post("", response_model=BodyweightLogResponse, status_code=status.HTTP_201_CREATED)
async def create_bodyweight_log(
    body: CreateBodyweightLogRequest,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BodyweightLog:
    """Record the current athlete's body weight (kg), timestamped now."""
    if not 0 < body.weight_kg < 1000:
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            ErrorCode.invalid_bodyweight_log,
            "Weight must be between 0 and 1000 kg",
        )

    log = BodyweightLog(athlete_id=user.id, weight_kg=body.weight_kg)
    session.add(log)
    await session.commit()
    await session.refresh(log)
    return log


@router.get("", response_model=Page[BodyweightLogResponse])
async def list_bodyweight_logs(
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    params: Annotated[PaginationParams, Query()],
) -> Page[BodyweightLogResponse]:
    """The current athlete's body-weight history, most recent first (paginated)."""
    total = await session.scalar(
        select(func.count()).select_from(BodyweightLog).where(BodyweightLog.athlete_id == user.id)
    )
    rows = await session.scalars(
        select(BodyweightLog)
        .where(BodyweightLog.athlete_id == user.id)
        .order_by(BodyweightLog.recorded_at.desc())
        .offset(params.offset)
        .limit(params.page_size)
    )
    return Page(
        items=[BodyweightLogResponse.model_validate(row) for row in rows.all()],
        total_count=total or 0,
    )


@router.get("/recent", response_model=list[BodyweightLogResponse])
async def recent_bodyweight_logs(
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[BodyweightLog]:
    """The athlete's last few measurements for the history graph, oldest first so
    the chart reads left-to-right. Fixed-size and independent of list pagination."""
    rows = await session.scalars(
        select(BodyweightLog)
        .where(BodyweightLog.athlete_id == user.id)
        .order_by(BodyweightLog.recorded_at.desc())
        .limit(GRAPH_POINTS)
    )
    return list(reversed(rows.all()))
