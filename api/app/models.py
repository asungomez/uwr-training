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
        TrainingSubtype.alactic,
    ),
}


class TrainingItemKind(enum.StrEnum):
    series = "series"
    note = "note"


class CardioSubtype(enum.StrEnum):
    aerobic = "aerobic"
    anaerobic = "anaerobic"
    alactic = "alactic"


class CardioItemKind(enum.StrEnum):
    block = "block"
    note = "note"


class CardioIntervalKind(enum.StrEnum):
    effort = "effort"
    rest = "rest"


class MesocyclePhase(enum.StrEnum):
    adaptation = "adaptation"
    accumulation = "accumulation"
    transmutation = "transmutation"
    realization = "realization"


class SessionLogAction(enum.StrEnum):
    """Whether the athlete did or skipped a prescribed exercise in a logged session."""

    done = "done"
    skipped = "skipped"


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
    # Trackable parameters (e.g. "Peso", "Tiempo"). Definitions only; athletes log
    # values against them later. Order is irrelevant — sorted by creation for stability.
    parameters: Mapped[list["ExerciseParameter"]] = relationship(
        back_populates="exercise",
        cascade="all, delete-orphan",
        order_by="ExerciseParameter.created_at",
    )


class ExerciseParameter(Base):
    """A trackable parameter of an exercise (e.g. "Peso", "Tiempo") — just its
    definition (name + optional description); recorded values come later."""

    __tablename__ = "exercise_parameters"
    __table_args__ = (UniqueConstraint("exercise_id", "name", name="uq_exercise_parameter_name"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str]
    description: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(_TZ, server_default=func.now())

    exercise: Mapped["Exercise"] = relationship(back_populates="parameters")


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
    # Ordering within a category+subtype. Deferrable so a reorder can shuffle rows
    # one-by-one within a transaction without tripping uniqueness mid-shuffle.
    __table_args__ = (
        UniqueConstraint(
            "category",
            "subtype",
            "position",
            name="uq_training_session_position",
            deferrable=True,
            initially="DEFERRED",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    category: Mapped[TrainingCategory]
    subtype: Mapped[TrainingSubtype]
    position: Mapped[int] = mapped_column(default=0, server_default="0")
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

    @property
    def exercise_name(self) -> str | None:
        """The linked exercise's name, for series items (None for notes). Requires
        the `exercise` relationship to be loaded."""
        return self.exercise.name if self.exercise is not None else None


class CardioTraining(Base):
    """A reusable cardio plan — a completely separate model from gym/pool's
    TrainingSession. It holds an ordered list of items (blocks and inter-block
    notes); each block is a round (a sequence of intervals) repeated N times."""

    __tablename__ = "cardio_trainings"
    # Ordering within a subtype, deferrable so a reorder can shuffle rows one-by-one
    # within a transaction without tripping uniqueness mid-shuffle.
    __table_args__ = (
        UniqueConstraint(
            "subtype",
            "position",
            name="uq_cardio_training_position",
            deferrable=True,
            initially="DEFERRED",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    subtype: Mapped[CardioSubtype]
    position: Mapped[int] = mapped_column(default=0, server_default="0")
    title: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(_TZ, server_default=func.now())

    items: Mapped[list["CardioItem"]] = relationship(
        back_populates="training",
        cascade="all, delete-orphan",
        order_by="CardioItem.position",
    )


class CardioItem(Base):
    """One entry in a cardio training's ordered list — either a `block` (a round
    repeated N times, with an optional trailing rest) or a free-text `note`
    ("10s descanso" between blocks). A single table + shared position lets notes
    sit between blocks."""

    __tablename__ = "cardio_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    training_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cardio_trainings.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[CardioItemKind]
    position: Mapped[int]

    # kind == block: the round (its intervals) is repeated `repeats` times, then an
    # optional `rest_seconds` rest at the end of the block.
    repeats: Mapped[int] = mapped_column(default=1, server_default="1")
    rest_seconds: Mapped[int | None] = mapped_column(default=None)

    # kind == note: free text shown between blocks.
    text: Mapped[str | None] = mapped_column(default=None)

    training: Mapped["CardioTraining"] = relationship(back_populates="items")
    intervals: Mapped[list["CardioInterval"]] = relationship(
        back_populates="item",
        cascade="all, delete-orphan",
        order_by="CardioInterval.position",
    )


class CardioInterval(Base):
    """One step of a block's round — either an `effort` (a duration at a given
    intensity %) or a `rest` (a duration). Ordered within its block."""

    __tablename__ = "cardio_intervals"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cardio_items.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[CardioIntervalKind]
    position: Mapped[int]
    duration_seconds: Mapped[int]
    # kind == effort: intensity as a percentage (60, 80, 90). Null for rests.
    intensity_pct: Mapped[int | None] = mapped_column(default=None)

    item: Mapped["CardioItem"] = relationship(back_populates="intervals")


class Week(Base):
    """An ordered planning week in the calendar. It holds how many sessions of each
    type (category+subtype) are recommended that week — NOT links to specific
    trainings, which vary per athlete. Belongs to a mesocycle phase."""

    __tablename__ = "weeks"
    # Ordering across the whole calendar, deferrable so a reorder can shuffle rows
    # one-by-one within a transaction without tripping uniqueness mid-shuffle.
    __table_args__ = (
        UniqueConstraint(
            "position",
            name="uq_week_position",
            deferrable=True,
            initially="DEFERRED",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str]
    position: Mapped[int] = mapped_column(default=0, server_default="0")
    # A free-text recommended date ("Semana del 3 de marzo"), no date management.
    recommended_date: Mapped[str | None] = mapped_column(default=None)
    phase: Mapped[MesocyclePhase]
    created_at: Mapped[datetime] = mapped_column(_TZ, server_default=func.now())

    requirements: Mapped[list["WeekRequirement"]] = relationship(
        back_populates="week",
        cascade="all, delete-orphan",
        order_by="WeekRequirement.position",
    )


class WeekRequirement(Base):
    """How many sessions of one type (category+subtype) a week recommends, e.g.
    2x pool/endurance. Ordered within its week for stable display."""

    __tablename__ = "week_requirements"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    week_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("weeks.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int]
    category: Mapped[TrainingCategory]
    subtype: Mapped[TrainingSubtype]
    count: Mapped[int]

    week: Mapped["Week"] = relationship(back_populates="requirements")


class SessionLog(Base):
    """A record of one athlete performing a training session once, with a timestamp
    and an optional note. Cascades away if the session is deleted."""

    __tablename__ = "session_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    training_session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("training_sessions.id", ondelete="CASCADE"), index=True
    )
    athlete_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    # The calendar week this log counts towards (optional, editable). SET NULL so
    # deleting a week doesn't lose the log, just its link.
    week_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("weeks.id", ondelete="SET NULL"), default=None, index=True
    )
    performed_at: Mapped[datetime] = mapped_column(_TZ, server_default=func.now())
    # Free-text note the athlete writes when finishing, to remember something.
    note: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(_TZ, server_default=func.now())

    entries: Mapped[list["SessionLogEntry"]] = relationship(
        back_populates="log",
        cascade="all, delete-orphan",
        order_by="SessionLogEntry.position",
    )
    training_session: Mapped["TrainingSession"] = relationship()
    week: Mapped["Week | None"] = relationship()


class SessionLogEntry(Base):
    """One logged exercise within a session log. `action` records whether it was
    done or skipped; for a done entry, `performed_exercise` is the exercise actually
    used (the prescribed one or a chosen alternative). Pure FKs — a log entry is
    deleted if its (planned or performed) exercise is deleted."""

    __tablename__ = "session_log_entries"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    log_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("session_logs.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int]
    action: Mapped[SessionLogAction]
    # The prescribed exercise for this item.
    planned_exercise_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"), index=True
    )
    # The exercise actually performed — the planned one or an alternative. Null when
    # the action is `skipped`.
    performed_exercise_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"), default=None
    )

    log: Mapped["SessionLog"] = relationship(back_populates="entries")
    planned_exercise: Mapped["Exercise"] = relationship(foreign_keys=[planned_exercise_id])
    performed_exercise: Mapped["Exercise | None"] = relationship(
        foreign_keys=[performed_exercise_id]
    )
    parameter_values: Mapped[list["SessionLogParameterValue"]] = relationship(
        back_populates="entry",
        cascade="all, delete-orphan",
        order_by="SessionLogParameterValue.position",
    )


class SessionLogParameterValue(Base):
    """A value the athlete entered for one of the performed exercise's parameters.
    Pure FK — deleted if the parameter is deleted."""

    __tablename__ = "session_log_parameter_values"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    entry_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("session_log_entries.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int]
    parameter_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exercise_parameters.id", ondelete="CASCADE"), index=True
    )
    value: Mapped[str]

    entry: Mapped["SessionLogEntry"] = relationship(back_populates="parameter_values")
    parameter: Mapped["ExerciseParameter"] = relationship()
