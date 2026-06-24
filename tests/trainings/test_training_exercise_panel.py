import re
from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import (
    Exercise,
    ExerciseRelation,
    TrainingBlock,
    TrainingItem,
    TrainingItemKind,
    TrainingSession,
    TrainingSubBlock,
    User,
)


def _training_with_exercise(
    create_training: Callable[..., TrainingSession], exercise: Exercise
) -> TrainingSession:
    return create_training(
        title="Sesión con panel",
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
                                exercise_id=exercise.id,
                                sets=4,
                            )
                        ],
                    )
                ],
            )
        ],
    )


def test_clicking_exercise_opens_panel_with_details(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a training whose series references an exercise that has a description.
    member = create_user(role="member", email="member@example.com")
    exercise = create_exercise(
        name="Sentadilla profunda", type="gym", description="Baja **controlada**."
    )
    training = _training_with_exercise(create_training, exercise)
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos/{training.id}")

    # When I click the exercise name in the training.
    page.get_by_role("button", name="Sentadilla profunda").click()

    # Then the URL carries ?ejercicio=<id> and a panel shows the full exercise.
    expect(page).to_have_url(re.compile(rf"\?ejercicio={exercise.id}$"))
    panel = page.get_by_role("dialog")
    expect(panel.get_by_role("heading", name="Sentadilla profunda")).to_be_visible()
    expect(panel.get_by_text("controlada")).to_be_visible()


def test_deep_link_with_param_opens_panel(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a training and its series' exercise.
    member = create_user(role="member", email="member@example.com")
    exercise = create_exercise(name="Press banca", type="gym")
    training = _training_with_exercise(create_training, exercise)
    log_in_as(member)

    # When I open the detail URL with ?ejercicio=<id> directly, the panel is open.
    page.goto(f"{app_url}/entrenamientos/{training.id}?ejercicio={exercise.id}")
    expect(page.get_by_role("dialog").get_by_role("heading", name="Press banca")).to_be_visible()


def test_navigating_to_related_replaces_panel(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a training exercise that has a related exercise.
    member = create_user(role="member", email="member@example.com")
    alternative = create_exercise(name="Zancada alterna", type="gym")
    exercise = create_exercise(
        name="Sentadilla con barra",
        type="gym",
        related=[
            ExerciseRelation(related_exercise_id=alternative.id, note="Variante", position=0)
        ],
    )
    training = _training_with_exercise(create_training, exercise)
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos/{training.id}?ejercicio={exercise.id}")

    panel = page.get_by_role("dialog")
    expect(panel.get_by_role("heading", name="Sentadilla con barra")).to_be_visible()

    # When I click the related exercise inside the panel.
    panel.get_by_role("button", name="Zancada alterna").click()

    # Then the param is replaced and the panel re-renders with the new exercise.
    expect(page).to_have_url(re.compile(rf"\?ejercicio={alternative.id}$"))
    expect(panel.get_by_role("heading", name="Zancada alterna")).to_be_visible()
    expect(panel.get_by_role("heading", name="Sentadilla con barra")).to_have_count(0)


def test_close_panel_clears_param(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given the panel open via the URL.
    member = create_user(role="member", email="member@example.com")
    exercise = create_exercise(name="Remo", type="gym")
    training = _training_with_exercise(create_training, exercise)
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos/{training.id}?ejercicio={exercise.id}")
    expect(page.get_by_role("dialog")).to_be_visible()

    # When I close it.
    page.get_by_role("dialog").get_by_role("button", name="Cerrar").click()

    # Then the param is gone and the panel is closed.
    expect(page).to_have_url(f"{app_url}/entrenamientos/{training.id}")
    expect(page.get_by_role("dialog")).to_have_count(0)
