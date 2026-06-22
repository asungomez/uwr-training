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
    password: str
