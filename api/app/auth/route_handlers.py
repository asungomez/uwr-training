import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import current_user, require_admin
from app.auth.schemas import (
    AcceptInvitationRequest,
    CreateInvitationRequest,
    DirectoryEntryResponse,
    DirectoryStatus,
    InvitationInfo,
    InvitationResponse,
    LoginRequest,
    UpdateUserRequest,
    UserDetailResponse,
    UserListParams,
    UserResponse,
)
from app.auth.utils import (
    clear_session_cookie,
    get_pending_invitation,
    set_session_cookie,
)
from app.db import get_session
from app.errors import ErrorCode, api_error
from app.models import Invitation, User, UserRole
from app.pagination import Page, paginate
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
        raise api_error(
            status.HTTP_401_UNAUTHORIZED, ErrorCode.invalid_credentials, "Invalid credentials"
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


@router.get("/users")
async def list_users(
    _admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
    params: Annotated[UserListParams, Query()],
) -> Page[DirectoryEntryResponse]:
    """Existing users plus invitations that haven't been accepted yet, optionally
    filtered. `status` scopes the result: active/inactive look at users only,
    invitation_pending/expired look at invitations only."""
    now = datetime.now(UTC)
    user_statuses = {DirectoryStatus.active, DirectoryStatus.inactive}
    invitation_statuses = {
        DirectoryStatus.invitation_pending,
        DirectoryStatus.invitation_expired,
    }
    include_users = params.status is None or params.status in user_statuses
    include_invitations = params.status is None or params.status in invitation_statuses

    entries: list[DirectoryEntryResponse] = []

    if include_users:
        users_query = select(User)
        if params.search:
            users_query = users_query.where(User.email.ilike(f"%{params.search.strip()}%"))
        if params.role is not None:
            users_query = users_query.where(User.role == params.role)
        if params.status == DirectoryStatus.active:
            users_query = users_query.where(User.is_active.is_(True))
        elif params.status == DirectoryStatus.inactive:
            users_query = users_query.where(User.is_active.is_(False))
        users = await session.scalars(users_query)
        entries += [
            DirectoryEntryResponse(
                id=user.id,
                email=user.email,
                role=user.role,
                status=(DirectoryStatus.active if user.is_active else DirectoryStatus.inactive),
            )
            for user in users
        ]

    if include_invitations:
        pending_query = select(Invitation).where(Invitation.accepted_at.is_(None))
        if params.search:
            pending_query = pending_query.where(
                Invitation.email.ilike(f"%{params.search.strip()}%")
            )
        if params.role is not None:
            pending_query = pending_query.where(Invitation.role == params.role)
        if params.status == DirectoryStatus.invitation_pending:
            pending_query = pending_query.where(Invitation.expires_at >= now)
        elif params.status == DirectoryStatus.invitation_expired:
            pending_query = pending_query.where(Invitation.expires_at < now)
        pending = await session.scalars(pending_query)
        entries += [
            DirectoryEntryResponse(
                id=invitation.id,
                email=invitation.email,
                role=invitation.role,
                status=(
                    DirectoryStatus.invitation_pending
                    if invitation.expires_at >= now
                    else DirectoryStatus.invitation_expired
                ),
            )
            for invitation in pending
        ]

    entries.sort(key=lambda entry: entry.email)
    return paginate(entries, params)


async def _inviter_email(session: AsyncSession, email: str) -> str | None:
    """Email of whoever invited the person with this email, or None if there was
    no invitation (e.g. created programmatically via the CLI)."""
    invitation = await session.scalar(select(Invitation).where(Invitation.email == email))
    if invitation is None:
        return None
    inviter = await session.get(User, invitation.invited_by)
    return inviter.email if inviter is not None else None


async def _user_detail(session: AsyncSession, user: User) -> UserDetailResponse:
    return UserDetailResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        status=DirectoryStatus.active if user.is_active else DirectoryStatus.inactive,
        created_at=user.created_at,
        invited_by_email=await _inviter_email(session, user.email),
    )


@router.get("/users/{entry_id}", response_model=UserDetailResponse)
async def get_user_detail(
    entry_id: uuid.UUID,
    _admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserDetailResponse:
    """Detail for a directory entry — the id may be a user or an invitation."""
    user = await session.get(User, entry_id)
    if user is not None:
        return await _user_detail(session, user)

    invitation = await session.get(Invitation, entry_id)
    if invitation is not None and invitation.accepted_at is None:
        is_pending = invitation.expires_at >= datetime.now(UTC)
        inviter = await session.get(User, invitation.invited_by)
        return UserDetailResponse(
            id=invitation.id,
            email=invitation.email,
            role=invitation.role,
            status=(
                DirectoryStatus.invitation_pending
                if is_pending
                else DirectoryStatus.invitation_expired
            ),
            invited_by_email=inviter.email if inviter is not None else None,
            expires_at=invitation.expires_at if is_pending else None,
        )

    raise api_error(status.HTTP_404_NOT_FOUND, ErrorCode.user_not_found, "User not found")


@router.patch("/users/{user_id}", response_model=UserDetailResponse)
async def update_user(
    user_id: uuid.UUID,
    body: UpdateUserRequest,
    _admin: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserDetailResponse:
    """Partially update a user. Only real users are updatable (not invitations)."""
    user = await session.get(User, user_id)
    if user is None:
        raise api_error(status.HTTP_404_NOT_FOUND, ErrorCode.user_not_found, "User not found")

    if body.status is not None:
        if body.status not in (DirectoryStatus.active, DirectoryStatus.inactive):
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.invalid_status,
                "A user's status can only be active or inactive",
            )
        user.is_active = body.status == DirectoryStatus.active

    await session.commit()
    await session.refresh(user)
    return await _user_detail(session, user)


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
        raise api_error(
            status.HTTP_409_CONFLICT,
            ErrorCode.email_already_exists,
            "A user with this email already exists",
        )

    existing_invitation = await session.scalar(select(Invitation).where(Invitation.email == email))
    if existing_invitation is not None:
        raise api_error(
            status.HTTP_409_CONFLICT,
            ErrorCode.invitation_already_exists,
            "An invitation for this email already exists",
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
        raise api_error(
            status.HTTP_409_CONFLICT,
            ErrorCode.email_already_exists,
            "A user with this email already exists",
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
