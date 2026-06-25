from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import (
    Exercise,
    ExerciseParameter,
    ExerciseRelation,
    TrainingBlock,
    TrainingItem,
    TrainingItemKind,
    TrainingSession,
    TrainingSubBlock,
    User,
)


def _make_training(
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
) -> TrainingSession:
    """A gym training with two series — a squat (with a 'Peso' parameter and one
    alternative) and a plank (no params/alternatives) — plus an inter-item note."""
    alt = create_exercise(name="Zancada", type="gym")
    squat = create_exercise(
        name="Sentadilla",
        type="gym",
        description="Baja **profunda**.",
        parameters=[ExerciseParameter(name="Peso", description="En kilos")],
        related=[ExerciseRelation(related_exercise_id=alt.id, note="sin barra", position=0)],
    )
    plank = create_exercise(name="Plancha", type="gym")
    return create_training(
        title="Sesión registrable",
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
                                kind=TrainingItemKind.series,
                                position=0,
                                exercise_id=squat.id,
                                sets=4,
                                reps=8,
                            ),
                            TrainingItem(
                                kind=TrainingItemKind.note, position=1, text="descanso 2min"
                            ),
                            TrainingItem(
                                kind=TrainingItemKind.series, position=2, exercise_id=plank.id
                            ),
                        ],
                    )
                ],
            )
        ],
    )


def test_start_button_opens_register(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    training = _make_training(create_exercise, create_training)
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos/{training.id}")

    page.get_by_role("link", name="Empezar").click()
    expect(page).to_have_url(f"{app_url}/entrenamientos/{training.id}/registrar")
    main = page.get_by_role("main")
    expect(main.get_by_role("heading", name="Registrar sesión")).to_be_visible()
    # The prescription + note context are shown, like the detail page.
    expect(main.get_by_text("Series:", exact=False)).to_be_visible()
    expect(main.get_by_text("descanso 2min")).to_be_visible()


def test_register_done_with_alternative_and_param(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    training = _make_training(create_exercise, create_training)
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos/{training.id}/registrar")

    # Switch the squat to its single alternative (switches directly).
    page.get_by_role("button", name="Cambiar a ejercicio alternativo").click()
    expect(page.get_by_text("Zancada")).to_be_visible()

    # Mark the squat done → its Peso input appears.
    page.get_by_role("button", name="Hecho").first.click()
    peso = page.get_by_label("Peso", exact=False)
    expect(peso).to_be_visible()
    peso.fill("80kg")

    # Skip the plank.
    page.get_by_role("button", name="No hecho").nth(1).click()

    # Add a note and finish.
    page.get_by_label("Nota de la sesión", exact=False).fill("buena sesión")
    page.get_by_role("button", name="Finalizar sesión").click()

    # Toast + back to the session detail.
    expect(page.get_by_role("status").filter(has_text="Sesión registrada.")).to_be_visible()
    expect(page).to_have_url(f"{app_url}/entrenamientos/{training.id}")


def test_register_opens_exercise_description_panel(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    training = _make_training(create_exercise, create_training)
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos/{training.id}/registrar")

    # Clicking the exercise name opens its full description in the side panel.
    page.get_by_role("button", name="Sentadilla").click()
    panel = page.get_by_role("dialog")
    expect(panel.get_by_role("heading", name="Sentadilla")).to_be_visible()
    expect(panel.get_by_text("profunda")).to_be_visible()
