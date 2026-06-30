import enum
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_serializer

from app.models import UserRole
from app.pagination import PaginationParams


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    role: UserRole
    is_active: bool

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)


class DirectoryStatus(enum.StrEnum):
    """Status shown in the admin users table — covers both real users and the
    pending/expired invitations that haven't become users yet."""

    active = "active"
    inactive = "inactive"
    invitation_pending = "invitation_pending"
    invitation_expired = "invitation_expired"


class UserListParams(PaginationParams):
    """Query params for the admin users directory: pagination + filters."""

    search: str | None = None
    role: UserRole | None = None
    status: DirectoryStatus | None = None


class DirectoryEntryResponse(BaseModel):
    """A row in the admin users table: an existing user or a pending invitation."""

    id: uuid.UUID
    email: str
    role: UserRole
    status: DirectoryStatus

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)


class UserDetailResponse(BaseModel):
    """Full detail for a single directory entry (a user or an invitation)."""

    id: uuid.UUID
    email: str
    role: UserRole
    status: DirectoryStatus
    # Only real users have a creation timestamp; null for invitations.
    created_at: datetime | None = None
    # Email of whoever invited them; null if created programmatically.
    invited_by_email: str | None = None
    # Only meaningful for a pending invitation; null otherwise.
    expires_at: datetime | None = None

    @field_serializer("id")
    def serialize_id(self, value: uuid.UUID) -> str:
        return str(value)


class UpdateUserRequest(BaseModel):
    """Partial update for a user. Only `status` for now; more fields can be added."""

    status: DirectoryStatus | None = None


class TrainingLogCategory(enum.StrEnum):
    """The kind of training a log belongs to, in the admin's per-user log view.
    Gym and pool are both `SessionLog`s told apart by their session's category;
    cardio is a separate model."""

    gym = "gym"
    pool = "pool"
    cardio = "cardio"


class TrainingLogListParams(PaginationParams):
    """Query params for an athlete's merged training-log history: pagination plus an
    optional category filter."""

    category: TrainingLogCategory | None = None


class TrainingLogSummaryResponse(BaseModel):
    """A row in the admin's per-user training-log history — one logged session of any
    kind, with just enough to show and link to it."""

    id: uuid.UUID
    category: TrainingLogCategory
    # The session/plan this log is for, so the row can deep-link to its detail.
    training_id: uuid.UUID
    training_title: str | None
    performed_at: datetime
    # Cardio's free-text activity ("running"); null for gym/pool.
    activity: str | None = None
    note: str | None = None

    @field_serializer("id", "training_id")
    def serialize_uuid(self, value: uuid.UUID) -> str:
        return str(value)


class CreateInvitationRequest(BaseModel):
    email: EmailStr


class InvitationResponse(BaseModel):
    """Returned once on creation. `token` is the raw value to share; it is never
    stored (only its hash) and cannot be retrieved again."""

    email: str
    role: UserRole
    token: str
    expires_at: datetime


class InvitationInfo(BaseModel):
    """Public details of a pending invitation, for the accept screen."""

    email: str
    role: UserRole


class AcceptInvitationRequest(BaseModel):
    # Email is verified against the invitation; the URL token alone isn't enough.
    email: EmailStr
    password: str


class ResetCodeResponse(BaseModel):
    """Returned once when an admin generates a reset code; only its hash is stored."""

    code: str
    expires_at: datetime


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    password: str
