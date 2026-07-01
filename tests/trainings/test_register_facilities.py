import uuid
from collections.abc import Callable

import sqlalchemy
from playwright.sync_api import Page, expect
from sqlalchemy.orm import Session

from app.models import (
    Exercise,
    ExerciseGymFacility,
    ExerciseRelation,
    GymFacility,
    TrainingBlock,
    TrainingItem,
    TrainingItemKind,
    TrainingSession,
    TrainingSubBlock,
    User,
)


def _seed_facilities(engine: sqlalchemy.Engine, *names: str) -> dict[str, uuid.UUID]:
    """Persist the named gym facilities (unique by name) and return name→id, so
    exercises can link them by id without re-inserting a shared one."""
    ids: dict[str, uuid.UUID] = {}
    with Session(engine, expire_on_commit=False) as session:
        for name in names:
            facility = GymFacility(name=name)
            session.add(facility)
            session.flush()
            ids[name] = facility.id
        session.commit()
    return ids


def _make_training(
    engine: sqlalchemy.Engine,
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
) -> TrainingSession:
    """A gym training whose one series needs 'Barra dominadas', with an alternative
    that needs 'Máquina remo' (so a swap replaces the facility)."""
    fac = _seed_facilities(engine, "Barra dominadas", "Máquina remo")
    alt = create_exercise(
        name="Remo en máquina",
        type="gym",
        gym_facilities=[ExerciseGymFacility(gym_facility_id=fac["Máquina remo"], position=0)],
    )
    pull = create_exercise(
        name="Dominadas",
        type="gym",
        gym_facilities=[ExerciseGymFacility(gym_facility_id=fac["Barra dominadas"], position=0)],
        related=[ExerciseRelation(related_exercise_id=alt.id, position=0)],
    )
    return create_training(
        title="Sesión con instalaciones",
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
                                kind=TrainingItemKind.series, position=0, exercise_id=pull.id
                            )
                        ],
                    )
                ],
            )
        ],
    )


def test_facilities_list_updates_with_alternative(
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

    # The facilities section lists the planned exercise's facility, with the note.
    section = page.get_by_role("heading", name="Instalaciones").locator("xpath=../ul")
    expect(section.get_by_text("Barra dominadas", exact=True)).to_be_visible()
    expect(section.get_by_text("Máquina remo", exact=True)).to_have_count(0)
    expect(
        page.get_by_text("La lista de instalaciones se actualiza si haces alguno de los ejercicios")
    ).to_be_visible()

    # Switching to the alternative replaces the facility.
    page.get_by_role("button", name="Cambiar a ejercicio alternativo").click()
    expect(section.get_by_text("Máquina remo", exact=True)).to_be_visible()
    expect(section.get_by_text("Barra dominadas", exact=True)).to_have_count(0)

    # Switching back restores the planned exercise's facility.
    page.get_by_role("button", name="Volver al estándar", exact=False).click()
    expect(section.get_by_text("Barra dominadas", exact=True)).to_be_visible()
    expect(section.get_by_text("Máquina remo", exact=True)).to_have_count(0)
