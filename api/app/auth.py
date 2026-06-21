import os
import uuid
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, EmailStr, field_serializer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import User, UserRole
from app.security import (
    SESSION_COOKIE,
    SESSION_MAX_AGE,
    create_session_token,
    decode_session_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# Secure cookie only over HTTPS in deployed envs; relaxed for local http dev.
_COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "true").lower() != "false"


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


@router.post("/login", response_model=UserResponse)
async def login(
    body: LoginRequest,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    email = body.email.strip().lower()
    user = await session.scalar(select(User).where(User.email == email))
    invalid = (
        user is None
        or not user.is_active
        or not verify_password(body.password, user.hashed_password)
    )
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    assert user is not None  # guaranteed by the `invalid` check above
    response.set_cookie(
        key=SESSION_COOKIE,
        value=create_session_token(str(user.id)),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=_COOKIE_SECURE,
        samesite="lax",
    )
    return user


async def current_user(
    session: Annotated[AsyncSession, Depends(get_session)],
    session_cookie: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> User:
    if session_cookie is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user_id = decode_session_token(session_cookie)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    return user


@router.get("/me", response_model=UserResponse)
async def me(user: Annotated[User, Depends(current_user)]) -> User:
    return user


@router.post("/logout")
async def logout(response: Response) -> dict[str, str]:
    response.delete_cookie(key=SESSION_COOKIE)
    return {"status": "ok"}
