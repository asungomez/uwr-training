"""Exercise factory. `build_exercise` returns an in-memory Exercise (not persisted).

Mandatory fields are auto-filled with Faker; pass overrides only for what the test
story cares about, e.g. build_exercise(name="Sentadilla", type="gym").
"""

from faker import Faker

from app.models import Exercise, ExerciseType

fake = Faker()


def build_exercise(
    *,
    type: ExerciseType | str = ExerciseType.gym,
    **overrides: object,
) -> Exercise:
    """Build an in-memory Exercise with all mandatory fields filled."""
    if isinstance(type, str):
        type = ExerciseType(type)
    fields: dict[str, object] = {
        "name": fake.unique.sentence(nb_words=2).rstrip("."),
        "type": type,
    }
    fields.update(overrides)
    return Exercise(**fields)
