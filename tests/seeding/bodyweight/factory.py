"""Bodyweight-log factory. `build_bodyweight_log` returns an in-memory
BodyweightLog (not persisted). Mandatory fields are auto-filled; pass overrides
for what the test story cares about, e.g. build_bodyweight_log(weight_kg=80)."""

from app.models import BodyweightLog


def build_bodyweight_log(*, weight_kg: float = 75.0, **overrides: object) -> BodyweightLog:
    """Build an in-memory BodyweightLog with all mandatory fields filled."""
    fields: dict[str, object] = {"weight_kg": weight_kg}
    fields.update(overrides)
    return BodyweightLog(**fields)
