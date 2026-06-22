from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import User, UserRole
from app.security import SESSION_COOKIE, decode_session_token


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


async def require_admin(user: Annotated[User, Depends(current_user)]) -> User:
    if user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return user
