from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import current_user, require_admin
from app.auth.schemas import (
    AcceptInvitationRequest,
    CreateInvitationRequest,
    InvitationInfo,
    InvitationResponse,
    LoginRequest,
    UserResponse,
)
from app.auth.utils import (
    clear_session_cookie,
    get_pending_invitation,
    set_session_cookie,
)
from app.db import get_session
from app.models import Invitation, User, UserRole
from app.security import (
    INVITATION_MAX_AGE,
    generate_invitation_token,
    hash_password,
    hash_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


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
    set_session_cookie(response, user)
    return user


@router.get("/me", response_model=UserResponse)
async def me(user: Annotated[User, Depends(current_user)]) -> User:
    return user


@router.post("/logout")
async def logout(response: Response) -> dict[str, str]:
    clear_session_cookie(response)
    return {"status": "ok"}


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    _admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[User]:
    result = await session.scalars(select(User).order_by(User.email))
    return list(result.all())


@router.post(
    "/invitations",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_invitation(
    body: CreateInvitationRequest,
    admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> InvitationResponse:
    email = body.email.strip().lower()

    existing_user = await session.scalar(select(User).where(User.email == email))
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    token = generate_invitation_token()
    expires_at = datetime.now(UTC) + INVITATION_MAX_AGE
    invitation = Invitation(
        email=email,
        token_hash=hash_token(token),
        role=UserRole.member,
        invited_by=admin.id,
        expires_at=expires_at,
    )
    session.add(invitation)
    await session.commit()

    return InvitationResponse(
        email=email,
        role=UserRole.member,
        token=token,
        expires_at=expires_at,
    )


@router.get("/invitations/{token}", response_model=InvitationInfo)
async def get_invitation(
    token: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Invitation:
    return await get_pending_invitation(token, session)


@router.post("/invitations/{token}/accept", response_model=UserResponse)
async def accept_invitation(
    token: str,
    body: AcceptInvitationRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    invitation = await get_pending_invitation(token, session)

    if await session.scalar(select(User).where(User.email == invitation.email)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    user = User(
        email=invitation.email,
        hashed_password=hash_password(body.password),
        role=invitation.role,
    )
    session.add(user)
    invitation.accepted_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(user)
    return user
