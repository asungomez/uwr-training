"""Week factory. `build_week` returns an in-memory Week (not persisted).

Mandatory fields are auto-filled; pass overrides only for what the test story
cares about, e.g. build_week(phase="accumulation").
"""

from faker import Faker

from app.models import MesocyclePhase, Week

fake = Faker()


def build_week(
    *,
    phase: MesocyclePhase | str = MesocyclePhase.adaptation,
    **overrides: object,
) -> Week:
    """Build an in-memory Week with all mandatory fields filled."""
    if isinstance(phase, str):
        phase = MesocyclePhase(phase)
    fields: dict[str, object] = {
        "name": fake.unique.sentence(nb_words=3).rstrip("."),
        "phase": phase,
    }
    fields.update(overrides)
    return Week(**fields)
