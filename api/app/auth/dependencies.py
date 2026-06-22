from typing import Annotated

from fastapi import Cookie, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.errors import ErrorCode, api_error
from app.models import User, UserRole
from app.security import SESSION_COOKIE, decode_session_token


async def current_user(
    session: Annotated[AsyncSession, Depends(get_session)],
    session_cookie: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> User:
    if session_cookie is None:
        raise api_error(
            status.HTTP_401_UNAUTHORIZED, ErrorCode.not_authenticated, "Not authenticated"
        )
    user_id = decode_session_token(session_cookie)
    if user_id is None:
        raise api_error(status.HTTP_401_UNAUTHORIZED, ErrorCode.invalid_session, "Invalid session")
    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        raise api_error(status.HTTP_401_UNAUTHORIZED, ErrorCode.invalid_session, "Invalid session")
    return user


async def require_admin(user: Annotated[User, Depends(current_user)]) -> User:
    if user.role != UserRole.admin:
        raise api_error(status.HTTP_403_FORBIDDEN, ErrorCode.admin_required, "Admin only")
    return user
