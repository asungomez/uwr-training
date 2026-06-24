"""CardioTraining factory. `build_cardio_training` returns an in-memory training
(not persisted).

Mandatory fields are auto-filled; pass overrides only for what the test story
cares about, e.g. build_cardio_training(subtype="anaerobic").
"""

from faker import Faker

from app.models import CardioSubtype, CardioTraining

fake = Faker()


def build_cardio_training(
    *,
    subtype: CardioSubtype | str = CardioSubtype.aerobic,
    **overrides: object,
) -> CardioTraining:
    """Build an in-memory CardioTraining with all mandatory fields filled."""
    if isinstance(subtype, str):
        subtype = CardioSubtype(subtype)
    fields: dict[str, object] = {
        "subtype": subtype,
        "title": fake.unique.sentence(nb_words=3).rstrip("."),
    }
    fields.update(overrides)
    return CardioTraining(**fields)
