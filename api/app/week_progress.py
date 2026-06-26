"""Shared week ↔ log logic, used by the weeks endpoints and both log flows
(gym/pool `SessionLog` and `CardioSessionLog`).

A week "recommends" a training type via a `WeekRequirement` (category+subtype). An
athlete's progress on a requirement counts their logs of that exact type linked to
that week — across both log tables. These helpers keep that counting in one place so
the calendar progress, the log-form dropdown, and the week recommendation all agree.
"""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_serializer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    CardioSessionLog,
    CardioTraining,
    SessionLog,
    StrengthTestLog,
    TrainingCategory,
    TrainingSession,
    TrainingSubtype,
    Week,
    WeekRequirement,
)


class WeekLogSummary(BaseModel):
    """A log (of the requesting athlete) that counts towards a requirement. `kind`
    tells gym/pool ("training") from cardio ("cardio") and strength tests ("test"),
    so the UI links to the right detail page. `training_id` is the TrainingSession or
    CardioTraining id — null for a strength test, which has no training entity."""

    log_id: uuid.UUID
    kind: Literal["training", "cardio", "test"]
    training_id: uuid.UUID | None
    training_title: str | None
    performed_at: datetime

    @field_serializer("log_id")
    def serialize_log_id(self, value: uuid.UUID) -> str:
        return str(value)

    @field_serializer("training_id")
    def serialize_training_id(self, value: uuid.UUID | None) -> str | None:
        return str(value) if value is not None else None


# The athlete's logs grouped by (week, category, subtype) — what a requirement counts.
type LogsByRequirement = dict[
    tuple[uuid.UUID, TrainingCategory, TrainingSubtype], list[WeekLogSummary]
]


async def logs_by_requirement(
    session: AsyncSession, week_ids: list[uuid.UUID], athlete_id: uuid.UUID
) -> LogsByRequirement:
    """For the given weeks, the athlete's logs linked to each — gym/pool and cardio —
    keyed by week + the log's training type (category+subtype). Most recent first."""
    grouped: LogsByRequirement = {}
    if not week_ids:
        return grouped

    # gym/pool logs: type comes from the linked TrainingSession.
    training_rows = await session.execute(
        select(SessionLog, TrainingSession)
        .join(TrainingSession, SessionLog.training_session_id == TrainingSession.id)
        .where(SessionLog.athlete_id == athlete_id, SessionLog.week_id.in_(week_ids))
        .order_by(SessionLog.performed_at.desc())
    )
    # cardio logs: category is always cardio; subtype from the CardioTraining.
    cardio_rows = await session.execute(
        select(CardioSessionLog, CardioTraining)
        .join(CardioTraining, CardioSessionLog.cardio_training_id == CardioTraining.id)
        .where(CardioSessionLog.athlete_id == athlete_id, CardioSessionLog.week_id.in_(week_ids))
        .order_by(CardioSessionLog.performed_at.desc())
    )
    # strength-test logs: always count as test/strength.
    test_rows = await session.scalars(
        select(StrengthTestLog)
        .where(StrengthTestLog.athlete_id == athlete_id, StrengthTestLog.week_id.in_(week_ids))
        .order_by(StrengthTestLog.performed_at.desc())
    )

    Row = tuple[uuid.UUID, TrainingCategory, TrainingSubtype, WeekLogSummary]
    rows: list[Row] = (
        [
            (
                log.week_id,
                training.category,
                training.subtype,
                WeekLogSummary(
                    log_id=log.id,
                    kind="training",
                    training_id=training.id,
                    training_title=training.title,
                    performed_at=log.performed_at,
                ),
            )
            for log, training in training_rows.all()
        ]
        + [
            (
                log.week_id,
                TrainingCategory.cardio,
                TrainingSubtype(training.subtype.value),
                WeekLogSummary(
                    log_id=log.id,
                    kind="cardio",
                    training_id=training.id,
                    training_title=training.title,
                    performed_at=log.performed_at,
                ),
            )
            for log, training in cardio_rows.all()
        ]
        + [
            (
                log.week_id,
                TrainingCategory.test,
                TrainingSubtype.strength,
                WeekLogSummary(
                    log_id=log.id,
                    kind="test",
                    training_id=None,
                    training_title="Prueba de fuerza",
                    performed_at=log.performed_at,
                ),
            )
            for log in test_rows.all()
        ]
    )

    # Merge, keeping most-recent-first order per key.
    rows.sort(key=lambda r: r[3].performed_at, reverse=True)
    for week_id, category, subtype, summary in rows:
        grouped.setdefault((week_id, category, subtype), []).append(summary)
    return grouped


async def weeks_recommending(
    session: AsyncSession, category: TrainingCategory, subtype: TrainingSubtype
) -> list[Week]:
    """Weeks whose requirements include this (category, subtype), ordered by position.
    These are the weeks a log of this type can be assigned to."""
    rows = await session.scalars(
        select(Week)
        .join(WeekRequirement, WeekRequirement.week_id == Week.id)
        .where(WeekRequirement.category == category, WeekRequirement.subtype == subtype)
        .order_by(Week.position)
        .distinct()
    )
    return list(rows.all())


async def incomplete_weeks_recommending(
    session: AsyncSession,
    category: TrainingCategory,
    subtype: TrainingSubtype,
    athlete_id: uuid.UUID,
) -> list[Week]:
    """The recommending weeks whose requirement for this type the athlete hasn't
    filled yet — fewer matching logs linked than recommended. Position-ordered."""
    weeks = await weeks_recommending(session, category, subtype)
    if not weeks:
        return weeks
    week_ids = [week.id for week in weeks]

    required: dict[uuid.UUID, int] = {}
    for week_id, count in (
        await session.execute(
            select(WeekRequirement.week_id, WeekRequirement.count).where(
                WeekRequirement.week_id.in_(week_ids),
                WeekRequirement.category == category,
                WeekRequirement.subtype == subtype,
            )
        )
    ).all():
        required[week_id] = count

    grouped = await logs_by_requirement(session, week_ids, athlete_id)
    return [
        week
        for week in weeks
        if len(grouped.get((week.id, category, subtype), [])) < required.get(week.id, 0)
    ]


async def latest_used_week(session: AsyncSession, athlete_id: uuid.UUID) -> Week | None:
    """The week the athlete most recently linked any logged session to (gym/pool or
    cardio, any type), or None. Compares the latest of each kind by timestamp."""
    training_row = (
        await session.execute(
            select(Week, SessionLog.performed_at)
            .join(SessionLog, SessionLog.week_id == Week.id)
            .where(SessionLog.athlete_id == athlete_id)
            .order_by(SessionLog.performed_at.desc())
            .limit(1)
        )
    ).first()
    cardio_row = (
        await session.execute(
            select(Week, CardioSessionLog.performed_at)
            .join(CardioSessionLog, CardioSessionLog.week_id == Week.id)
            .where(CardioSessionLog.athlete_id == athlete_id)
            .order_by(CardioSessionLog.performed_at.desc())
            .limit(1)
        )
    ).first()
    test_row = (
        await session.execute(
            select(Week, StrengthTestLog.performed_at)
            .join(StrengthTestLog, StrengthTestLog.week_id == Week.id)
            .where(StrengthTestLog.athlete_id == athlete_id)
            .order_by(StrengthTestLog.performed_at.desc())
            .limit(1)
        )
    ).first()
    candidates = [row for row in (training_row, cardio_row, test_row) if row is not None]
    if not candidates:
        return None
    week: Week = max(candidates, key=lambda row: row[1])[0]
    return week


def recommended_week_id(latest: Week | None, selectable: list[Week]) -> uuid.UUID | None:
    """Which selectable week to pre-select, given the athlete's latest-used week:
    that week if it's still selectable, else the next selectable one after it by
    position (e.g. latest week 3, selectable 1,2,5,7 → 5), else nothing."""
    if latest is None:
        return None
    if any(week.id == latest.id for week in selectable):
        return latest.id
    nxt = next((week for week in selectable if week.position > latest.position), None)
    return nxt.id if nxt is not None else None
