"""TrainingSession factory. `build_training` returns an in-memory session (not
persisted).

Mandatory fields are auto-filled; pass overrides only for what the test story
cares about, e.g. build_training(category="pool", subtype="endurance").
"""

from faker import Faker

from app.models import TrainingCategory, TrainingSession, TrainingSubtype

fake = Faker()


def build_training(
    *,
    category: TrainingCategory | str = TrainingCategory.gym,
    subtype: TrainingSubtype | str = TrainingSubtype.accumulation,
    **overrides: object,
) -> TrainingSession:
    """Build an in-memory TrainingSession with all mandatory fields filled."""
    if isinstance(category, str):
        category = TrainingCategory(category)
    if isinstance(subtype, str):
        subtype = TrainingSubtype(subtype)
    fields: dict[str, object] = {
        "category": category,
        "subtype": subtype,
        "title": fake.unique.sentence(nb_words=3).rstrip("."),
    }
    fields.update(overrides)
    return TrainingSession(**fields)
