import enum

from fastapi import HTTPException


class ErrorCode(enum.StrEnum):
    """Stable, language-agnostic identifiers for API errors. The front-end maps
    these to localized (Spanish) messages; the `message` is for debugging only."""

    not_authenticated = "not_authenticated"
    invalid_session = "invalid_session"
    invalid_credentials = "invalid_credentials"
    admin_required = "admin_required"
    email_already_exists = "email_already_exists"
    invitation_already_exists = "invitation_already_exists"
    invitation_not_found = "invitation_not_found"
    invitation_expired = "invitation_expired"


def api_error(status_code: int, code: ErrorCode, message: str) -> HTTPException:
    """Build an HTTPException whose body is {"detail": {"code", "message"}}."""
    return HTTPException(
        status_code=status_code,
        detail={"code": code.value, "message": message},
    )
