import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

# timestamptz everywhere — store and return timezone-aware datetimes.
_TZ = DateTime(timezone=True)


class UserRole(enum.Enum):
    admin = "admin"
    member = "member"


class ExerciseType(enum.StrEnum):
    gym = "gym"
    pool = "pool"


class TrainingCategory(enum.StrEnum):
    gym = "gym"
    pool = "pool"
    cardio = "cardio"


class TrainingSubtype(enum.StrEnum):
    # gym
    adaptation = "adaptation"
    accumulation = "accumulation"
    transmutation = "transmutation"
    realization = "realization"
    # pool
    endurance = "endurance"
    alactic = "alactic"
    # cardio
    aerobic = "aerobic"
    # shared by pool and cardio
    anaerobic = "anaerobic"


# Which subtypes are valid for each category (enforced in the API layer).
SUBTYPES_BY_CATEGORY: dict[TrainingCategory, tuple[TrainingSubtype, ...]] = {
    TrainingCategory.gym: (
        TrainingSubtype.adaptation,
        TrainingSubtype.accumulation,
        TrainingSubtype.transmutation,
        TrainingSubtype.realization,
    ),
    TrainingCategory.pool: (
        TrainingSubtype.endurance,
        TrainingSubtype.anaerobic,
        TrainingSubtype.alactic,
    ),
    TrainingCategory.cardio: (
        TrainingSubtype.aerobic,
        TrainingSubtype.anaerobic,
    ),
}


class TrainingItemKind(enum.StrEnum):
    series = "series"
    note = "note"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    hashed_password: Mapped[str]
    role: Mapped[UserRole]
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")
    # Admin-issued password-reset code (sha256 hash; plaintext shown once on generation).
    reset_code_hash: Mapped[str | None] = mapped_column(default=None)
    reset_code_expires_at: Mapped[datetime | None] = mapped_column(_TZ, default=None)
    created_at: Mapped[datetime] = mapped_column(_TZ, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        _TZ,
        server_default=func.now(),
        onupdate=func.now(),
    )


class Invitation(Base):
    __tablename__ = "invitations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    token_hash: Mapped[str] = mapped_column(unique=True, index=True)
    role: Mapped[UserRole]
    invited_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    expires_at: Mapped[datetime] = mapped_column(_TZ)
    accepted_at: Mapped[datetime | None] = mapped_column(_TZ, default=None)
    created_at: Mapped[datetime] = mapped_column(_TZ, server_default=func.now())


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(unique=True, index=True)
    description: Mapped[str | None] = mapped_column(default=None)
    type: Mapped[ExerciseType]
    # S3 object keys for optional media; URLs are built at serialization time.
    thumbnail_key: Mapped[str | None] = mapped_column(default=None)
    video_key: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(_TZ, server_default=func.now())

    # Alternative/related exercises (directional), each with a note. Ordered.
    related: Mapped[list["ExerciseRelation"]] = relationship(
        back_populates="exercise",
        foreign_keys="ExerciseRelation.exercise_id",
        cascade="all, delete-orphan",
        order_by="ExerciseRelation.position",
    )


class ExerciseRelation(Base):
    """A directional link from one exercise to an alternative/related one, with a
    note explaining when or why to use it (e.g. "si no tienes barra de dominadas…").
    """

    __tablename__ = "exercise_relations"
    __table_args__ = (
        UniqueConstraint("exercise_id", "related_exercise_id", name="uq_exercise_relation"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"), index=True
    )
    related_exercise_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"), index=True
    )
    note: Mapped[str | None] = mapped_column(default=None)
    position: Mapped[int] = mapped_column(default=0)

    exercise: Mapped["Exercise"] = relationship(
        back_populates="related", foreign_keys=[exercise_id]
    )
    related_exercise: Mapped["Exercise"] = relationship(foreign_keys=[related_exercise_id])


class TrainingSession(Base):
    """A reusable training plan. gym/pool sessions hold an ordered tree of blocks →
    sub-blocks → items; cardio sessions are modeled separately (no blocks yet).
    Sessions are NOT dated — when an athlete completes one is recorded per-athlete
    later, not on the plan itself."""

    __tablename__ = "training_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    category: Mapped[TrainingCategory]
    subtype: Mapped[TrainingSubtype]
    title: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(_TZ, server_default=func.now())

    blocks: Mapped[list["TrainingBlock"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="TrainingBlock.position",
    )


class TrainingBlock(Base):
    """An ordered section of a session (e.g. Calentamiento, Tren superior, Apnea)."""

    __tablename__ = "training_blocks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("training_sessions.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str]
    position: Mapped[int]

    session: Mapped["TrainingSession"] = relationship(back_populates="blocks")
    sub_blocks: Mapped[list["TrainingSubBlock"]] = relationship(
        back_populates="block",
        cascade="all, delete-orphan",
        order_by="TrainingSubBlock.position",
    )


class TrainingSubBlock(Base):
    """An ordered section of a block (e.g. Preparación, Principal, Descanso activo),
    holding the actual series and notes."""

    __tablename__ = "training_sub_blocks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    block_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("training_blocks.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str]
    position: Mapped[int]
    # Free-text note about the whole sub-block ("Repetir 3 veces", "Hacer con
    # aletas de fibra"), distinct from the inter-series notes among its items.
    notes: Mapped[str | None] = mapped_column(default=None)

    block: Mapped["TrainingBlock"] = relationship(back_populates="sub_blocks")
    items: Mapped[list["TrainingItem"]] = relationship(
        back_populates="sub_block",
        cascade="all, delete-orphan",
        order_by="TrainingItem.position",
    )


class TrainingItem(Base):
    """One entry in a sub-block's ordered list — either a `series` (an exercise
    with a prescription) or a free-text `note` ("10s descanso", "quítate las
    aletas"). A single table + shared position lets notes sit between series."""

    __tablename__ = "training_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    sub_block_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("training_sub_blocks.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[TrainingItemKind]
    position: Mapped[int]

    # kind == series: an exercise plus an all-optional prescription. The exercise
    # FK restricts deletion so an exercise used in a training can't vanish.
    exercise_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("exercises.id", ondelete="RESTRICT"), default=None
    )
    sets: Mapped[int | None] = mapped_column(default=None)
    reps: Mapped[int | None] = mapped_column(default=None)
    duration_seconds: Mapped[int | None] = mapped_column(default=None)
    distance_meters: Mapped[int | None] = mapped_column(default=None)
    effort: Mapped[str | None] = mapped_column(default=None)

    # kind == note: free text shown between series.
    text: Mapped[str | None] = mapped_column(default=None)

    sub_block: Mapped["TrainingSubBlock"] = relationship(back_populates="items")
    exercise: Mapped["Exercise | None"] = relationship()
