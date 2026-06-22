import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_serializer

from app.models import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    role: UserRole

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
