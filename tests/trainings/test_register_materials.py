import uuid
from collections.abc import Callable

import sqlalchemy
from playwright.sync_api import Page, expect
from sqlalchemy.orm import Session

from app.models import (
    Exercise,
    ExerciseGymMaterial,
    ExerciseRelation,
    GymMaterial,
    TrainingBlock,
    TrainingItem,
    TrainingItemKind,
    TrainingSession,
    TrainingSubBlock,
    User,
)


def _seed_materials(engine: sqlalchemy.Engine, *names: str) -> dict[str, uuid.UUID]:
    """Persist the named gym materials (unique by name) and return name→id, so
    exercises can link them by id without re-inserting a shared one."""
    ids: dict[str, uuid.UUID] = {}
    with Session(engine, expire_on_commit=False) as session:
        for name in names:
            material = GymMaterial(name=name)
            session.add(material)
            session.flush()
            ids[name] = material.id
        session.commit()
    return ids


def _make_training(
    engine: sqlalchemy.Engine,
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
) -> TrainingSession:
    """A gym training whose one series uses 'Barra' + 'Banco', with an alternative
    that uses 'Mancuernas' + 'Banco' (so a swap drops Barra and adds Mancuernas,
    keeping the shared Banco). 'Banco' is one shared material row, reused by both."""
    mat = _seed_materials(engine, "Barra", "Mancuernas", "Banco")
    alt = create_exercise(
        name="Press mancuernas",
        type="gym",
        gym_materials=[
            ExerciseGymMaterial(gym_material_id=mat["Mancuernas"], position=0),
            ExerciseGymMaterial(gym_material_id=mat["Banco"], position=1),
        ],
    )
    press = create_exercise(
        name="Press banca",
        type="gym",
        gym_materials=[
            ExerciseGymMaterial(gym_material_id=mat["Barra"], position=0),
            ExerciseGymMaterial(gym_material_id=mat["Banco"], position=1),
        ],
        related=[ExerciseRelation(related_exercise_id=alt.id, position=0)],
    )
    return create_training(
        title="Sesión con materiales",
        category="gym",
        subtype="accumulation",
        blocks=[
            TrainingBlock(
                name="Bloque",
                position=0,
                sub_blocks=[
                    TrainingSubBlock(
                        name="Sub",
                        position=0,
                        items=[
                            TrainingItem(
                                kind=TrainingItemKind.series, position=0, exercise_id=press.id
                            )
                        ],
                    )
                ],
            )
        ],
    )


def test_materials_list_updates_with_alternative(
    page: Page,
    app_url: str,
    _db_engine: sqlalchemy.Engine,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    training = _make_training(_db_engine, create_exercise, create_training)
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos/{training.id}/registrar")

    # The materials section lists the planned exercise's materials, with the note.
    section = page.get_by_role("heading", name="Materiales").locator("xpath=../ul")
    expect(section.get_by_text("Barra", exact=True)).to_be_visible()
    expect(section.get_by_text("Banco", exact=True)).to_be_visible()
    expect(section.get_by_text("Mancuernas", exact=True)).to_have_count(0)
    expect(
        page.get_by_text("La lista de materiales se actualiza si haces alguno de los ejercicios")
    ).to_be_visible()

    # Switching to the alternative drops Barra and adds Mancuernas; Banco (shared) stays.
    page.get_by_role("button", name="Cambiar a ejercicio alternativo").click()
    expect(section.get_by_text("Mancuernas", exact=True)).to_be_visible()
    expect(section.get_by_text("Banco", exact=True)).to_be_visible()
    expect(section.get_by_text("Barra", exact=True)).to_have_count(0)

    # Switching back restores the planned exercise's materials.
    page.get_by_role("button", name="Volver al estándar", exact=False).click()
    expect(section.get_by_text("Barra", exact=True)).to_be_visible()
    expect(section.get_by_text("Mancuernas", exact=True)).to_have_count(0)


def test_no_materials_section_when_exercises_have_none(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    plank = create_exercise(name="Plancha", type="gym")
    training = create_training(
        title="Sin materiales",
        category="gym",
        subtype="accumulation",
        blocks=[
            TrainingBlock(
                name="Bloque",
                position=0,
                sub_blocks=[
                    TrainingSubBlock(
                        name="Sub",
                        position=0,
                        items=[
                            TrainingItem(
                                kind=TrainingItemKind.series, position=0, exercise_id=plank.id
                            )
                        ],
                    )
                ],
            )
        ],
    )
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos/{training.id}/registrar")

    expect(page.get_by_role("heading", name="Registrar sesión")).to_be_visible()
    expect(page.get_by_role("heading", name="Materiales")).not_to_be_visible()
