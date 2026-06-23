import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.settings import settings

_ALGORITHM = "HS256"

SESSION_COOKIE = "session"
SESSION_MAX_AGE = 60 * 60 * 24 * 7  # 7 days, in seconds

INVITATION_MAX_AGE = timedelta(days=7)
RESET_CODE_MAX_AGE = timedelta(hours=24)
# Unambiguous uppercase alphanumerics (no O/0/I/1) — easy to read out / text.
_RESET_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
RESET_CODE_LENGTH = 8


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def generate_invitation_token() -> str:
    """A URL-safe random token; only the hash is stored, the raw value is emailed/shared."""
    return secrets.token_urlsafe(32)


def generate_reset_code() -> str:
    """A short human-friendly password-reset code; only its hash is stored."""
    return "".join(secrets.choice(_RESET_CODE_ALPHABET) for _ in range(RESET_CODE_LENGTH))


def hash_token(token: str) -> str:
    """Deterministic hash for invitation tokens (so we can look them up by hash)."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_session_token(user_id: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(seconds=SESSION_MAX_AGE),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=_ALGORITHM)


def decode_session_token(token: str) -> str | None:
    """Return the user id from a valid token, or None if invalid/expired."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[_ALGORITHM])
    except jwt.InvalidTokenError:
        return None
    sub = payload.get("sub")
    return sub if isinstance(sub, str) else None
