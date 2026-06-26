import enum

from fastapi import HTTPException


class ErrorCode(enum.StrEnum):
    """Stable, language-agnostic identifiers for API errors. The front-end maps
    these to localized (Spanish) messages; the `message` is for debugging only."""

    not_authenticated = "not_authenticated"
    invalid_session = "invalid_session"
    invalid_credentials = "invalid_credentials"
    admin_required = "admin_required"
    user_not_found = "user_not_found"
    invalid_status = "invalid_status"
    invalid_reset_code = "invalid_reset_code"
    email_already_exists = "email_already_exists"
    invitation_already_exists = "invitation_already_exists"
    invitation_already_accepted = "invitation_already_accepted"
    invitation_email_mismatch = "invitation_email_mismatch"
    invitation_not_found = "invitation_not_found"
    invitation_expired = "invitation_expired"
    exercise_already_exists = "exercise_already_exists"
    exercise_not_found = "exercise_not_found"
    invalid_media_type = "invalid_media_type"
    invalid_training_subtype = "invalid_training_subtype"
    invalid_related_exercise = "invalid_related_exercise"
    invalid_parameter = "invalid_parameter"
    invalid_block = "invalid_block"
    invalid_item = "invalid_item"
    training_not_found = "training_not_found"
    cardio_training_not_found = "cardio_training_not_found"
    invalid_cardio_block = "invalid_cardio_block"
    week_not_found = "week_not_found"
    invalid_week = "invalid_week"
    invalid_session_log = "invalid_session_log"
    session_log_not_found = "session_log_not_found"
    invalid_cardio_log = "invalid_cardio_log"
    cardio_log_not_found = "cardio_log_not_found"
    invalid_bodyweight_log = "invalid_bodyweight_log"


def api_error(status_code: int, code: ErrorCode, message: str) -> HTTPException:
    """Build an HTTPException whose body is {"detail": {"code", "message"}}."""
    return HTTPException(
        status_code=status_code,
        detail={"code": code.value, "message": message},
    )
