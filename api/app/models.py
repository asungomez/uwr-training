import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

# timestamptz everywhere — store and return timezone-aware datetimes.
_TZ = DateTime(timezone=True)


class UserRole(enum.Enum):
    admin = "admin"
    member = "member"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    hashed_password: Mapped[str]
    role: Mapped[UserRole]
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")
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
