from datetime import UTC, datetime

from fastapi import HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Invitation, User
from app.security import (
    SESSION_COOKIE,
    SESSION_MAX_AGE,
    create_session_token,
    hash_token,
)
from app.settings import settings


def set_session_cookie(response: Response, user: User) -> None:
    response.set_cookie(
        key=SESSION_COOKIE,
        value=create_session_token(str(user.id)),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=SESSION_COOKIE)


async def get_pending_invitation(token: str, session: AsyncSession) -> Invitation:
    """Look up a usable invitation by raw token, or raise 404/410."""
    invitation = await session.scalar(
        select(Invitation).where(Invitation.token_hash == hash_token(token))
    )
    if invitation is None or invitation.accepted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )
    if invitation.expires_at < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Invitation has expired",
        )
    return invitation
