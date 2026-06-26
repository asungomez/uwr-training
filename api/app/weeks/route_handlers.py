import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import current_user, require_admin
from app.db import get_session
from app.errors import ErrorCode, api_error
from app.models import (
    SUBTYPES_BY_CATEGORY,
    TrainingCategory,
    TrainingSubtype,
    User,
    Week,
    WeekRequirement,
)
from app.pagination import Page
from app.week_progress import LogsByRequirement, logs_by_requirement
from app.weeks.schemas import (
    CreateWeekRequest,
    RequirementDetail,
    RequirementInput,
    RequirementProgress,
    UpdateWeekPositionRequest,
    UpdateWeekRequest,
    WeekDetailResponse,
    WeekListParams,
    WeekResponse,
)

router = APIRouter(prefix="/weeks", tags=["weeks"])


def _build_requirements(requirements: list[RequirementInput]) -> list[WeekRequirement]:
    """Build ordered WeekRequirement rows from the submitted list. Rejects a
    subtype that doesn't belong to its category, or a non-positive count. Each test
    (e.g. strength, speed) is a single event: its count is always 1, and a week can
    have at most one of each test subtype (though it may mix different ones)."""
    rows: list[WeekRequirement] = []
    seen_test_subtypes: set[TrainingSubtype] = set()
    for position, item in enumerate(requirements):
        if item.subtype not in SUBTYPES_BY_CATEGORY[item.category]:
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.invalid_week,
                f"Subtype {item.subtype.value} is not valid for category {item.category.value}",
            )
        count = item.count
        if item.category is TrainingCategory.test:
            if item.subtype in seen_test_subtypes:
                raise api_error(
                    status.HTTP_400_BAD_REQUEST,
                    ErrorCode.invalid_week,
                    "A week can have at most one of each test",
                )
            seen_test_subtypes.add(item.subtype)
            count = 1  # a test is always a single event, ignore any submitted count
        elif count < 1:
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.invalid_week,
                "Each requirement needs a count of at least 1",
            )
        rows.append(
            WeekRequirement(
                position=position,
                category=item.category,
                subtype=item.subtype,
                count=count,
            )
        )
    return rows


async def _next_position(session: AsyncSession) -> int:
    """The next free position at the end of the calendar."""
    max_position = await session.scalar(select(func.max(Week.position)))
    return 0 if max_position is None else max_position + 1


async def _load_with_requirements(session: AsyncSession, week_id: uuid.UUID) -> Week | None:
    """Fetch a week with its requirements (ordered) loaded."""
    week: Week | None = await session.scalar(
        select(Week).where(Week.id == week_id).options(selectinload(Week.requirements))
    )
    return week


def _progress(req: WeekRequirement, grouped: LogsByRequirement) -> RequirementProgress:
    logs = grouped.get((req.week_id, req.category, req.subtype), [])
    return RequirementProgress(
        id=req.id,
        category=req.category,
        subtype=req.subtype,
        count=req.count,
        completed=min(req.count, len(logs)),
    )


def _requirement_detail(req: WeekRequirement, grouped: LogsByRequirement) -> RequirementDetail:
    logs = grouped.get((req.week_id, req.category, req.subtype), [])
    return RequirementDetail(
        id=req.id,
        category=req.category,
        subtype=req.subtype,
        count=req.count,
        completed=min(req.count, len(logs)),
        logs=logs,
    )


def _week_response(week: Week, grouped: LogsByRequirement) -> WeekResponse:
    return WeekResponse(
        id=week.id,
        name=week.name,
        position=week.position,
        recommended_date=week.recommended_date,
        phase=week.phase,
        created_at=week.created_at,
        requirements=[_progress(req, grouped) for req in week.requirements],
    )


def _week_detail(week: Week, grouped: LogsByRequirement) -> WeekDetailResponse:
    return WeekDetailResponse(
        id=week.id,
        name=week.name,
        position=week.position,
        recommended_date=week.recommended_date,
        phase=week.phase,
        created_at=week.created_at,
        requirements=[_requirement_detail(req, grouped) for req in week.requirements],
    )


@router.get("")
async def list_weeks(
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    params: Annotated[WeekListParams, Query()],
) -> Page[WeekResponse]:
    """All weeks in order, each with the athlete's progress per requirement.
    Filterable by name search and phase. Visible to any authenticated user."""
    filters: list[ColumnElement[bool]] = []
    if params.search:
        filters.append(Week.name.ilike(f"%{params.search.strip()}%"))
    if params.phase is not None:
        filters.append(Week.phase == params.phase)

    total = await session.scalar(select(func.count()).select_from(Week).where(*filters))
    weeks = list(
        await session.scalars(
            select(Week)
            .where(*filters)
            .order_by(Week.position)
            .offset(params.offset)
            .limit(params.page_size)
            .options(selectinload(Week.requirements))
        )
    )
    grouped = await logs_by_requirement(session, [week.id for week in weeks], user.id)
    return Page(
        items=[_week_response(week, grouped) for week in weeks],
        total_count=total or 0,
    )


@router.get("/{week_id}", response_model=WeekDetailResponse)
async def get_week(
    week_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> WeekDetailResponse:
    """A single week with each requirement's progress and the logs that fulfil it
    (the athlete's own). Visible to any user."""
    week = await _load_with_requirements(session, week_id)
    if week is None:
        raise api_error(status.HTTP_404_NOT_FOUND, ErrorCode.week_not_found, "Week not found")
    grouped = await logs_by_requirement(session, [week.id], user.id)
    return _week_detail(week, grouped)


@router.post("", response_model=WeekDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_week(
    body: CreateWeekRequest,
    user: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> WeekDetailResponse:
    name = body.name.strip()
    if not name:
        raise api_error(status.HTTP_400_BAD_REQUEST, ErrorCode.invalid_week, "Name is required")
    recommended_date = body.recommended_date.strip() if body.recommended_date else None
    week = Week(
        name=name,
        position=await _next_position(session),
        recommended_date=recommended_date or None,
        phase=body.phase,
    )
    week.requirements = _build_requirements(body.requirements)
    session.add(week)
    await session.commit()

    reloaded = await _load_with_requirements(session, week.id)
    assert reloaded is not None
    grouped = await logs_by_requirement(session, [reloaded.id], user.id)
    return _week_detail(reloaded, grouped)


@router.put("/{week_id}", response_model=WeekDetailResponse)
async def update_week(
    week_id: uuid.UUID,
    body: UpdateWeekRequest,
    user: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> WeekDetailResponse:
    week = await _load_with_requirements(session, week_id)
    if week is None:
        raise api_error(status.HTTP_404_NOT_FOUND, ErrorCode.week_not_found, "Week not found")

    name = body.name.strip()
    if not name:
        raise api_error(status.HTTP_400_BAD_REQUEST, ErrorCode.invalid_week, "Name is required")
    recommended_date = body.recommended_date.strip() if body.recommended_date else None
    week.name = name
    week.recommended_date = recommended_date or None
    week.phase = body.phase
    # Replace the requirement list wholesale with the submitted (ordered) one.
    week.requirements = _build_requirements(body.requirements)
    await session.commit()

    reloaded = await _load_with_requirements(session, week_id)
    assert reloaded is not None
    grouped = await logs_by_requirement(session, [reloaded.id], user.id)
    return _week_detail(reloaded, grouped)


@router.patch("/{week_id}/position", response_model=WeekResponse)
async def reorder_week(
    week_id: uuid.UUID,
    body: UpdateWeekPositionRequest,
    _admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Week:
    """Move a week to a new 0-based position; the rest of the calendar shifts to
    stay a contiguous 0..n-1 sequence."""
    week = await session.get(Week, week_id)
    if week is None:
        raise api_error(status.HTTP_404_NOT_FOUND, ErrorCode.week_not_found, "Week not found")

    # All weeks, in current order.
    scope = list(await session.scalars(select(Week).order_by(Week.position)))

    # Re-insert the moved week at the clamped target index, then renumber.
    target = max(0, min(body.position, len(scope) - 1))
    scope.remove(week)
    scope.insert(target, week)
    for index, item in enumerate(scope):
        item.position = index
    # The deferrable unique constraint is checked at commit, so the renumber above
    # can transiently repeat positions without erroring.
    await session.commit()
    await session.refresh(week)
    return week


@router.delete("/{week_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_week(
    week_id: uuid.UUID,
    _admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    week = await session.get(Week, week_id)
    if week is None:
        raise api_error(status.HTTP_404_NOT_FOUND, ErrorCode.week_not_found, "Week not found")
    await session.delete(week)
    await session.commit()
