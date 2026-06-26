from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import (
    Exercise,
    StrengthTestItem,
    StrengthTestLog,
    TrainingBlock,
    TrainingItem,
    TrainingItemKind,
    TrainingSession,
    TrainingSubBlock,
    User,
)


def _series(exercise: Exercise, position: int, **fields: object) -> TrainingItem:
    return TrainingItem(
        kind=TrainingItemKind.series,
        position=position,
        exercise_id=exercise.id,
        **fields,
    )


def _training_with(exercise: Exercise, create_training: Callable[..., TrainingSession], **fields):
    return create_training(
        title="Fuerza",
        category="gym",
        subtype="accumulation",
        blocks=[
            TrainingBlock(
                name="Bloque",
                position=0,
                sub_blocks=[
                    TrainingSubBlock(
                        name="Sub", position=0, items=[_series(exercise, 0, **fields)]
                    )
                ],
            )
        ],
    )


def test_load_field_only_for_tested_exercises(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_strength_test_item: Callable[..., StrengthTestItem],
    log_in_as: Callable[[User], None],
) -> None:
    admin = create_user(role="admin", email="admin@example.com")
    tested = create_exercise(name="Peso muerto", type="gym")
    untested = create_exercise(name="Flexiones", type="gym")
    create_strength_test_item(exercise_id=tested.id, weight_multiplier=1.5)
    log_in_as(admin)

    page.goto(f"{app_url}/entrenamientos/gimnasio/acumulacion/nuevo")
    page.get_by_label("Título").fill("Sesión")
    page.get_by_role("button", name="Añadir bloque").click()
    page.get_by_label("Nombre del bloque").fill("Bloque")
    page.get_by_role("button", name="Añadir sub-bloque").click()
    page.get_by_label("Nombre del sub-bloque").fill("Sub")

    # Untested exercise → no "Carga (%)" field.
    page.get_by_role("button", name="Añadir ejercicio").click()
    page.get_by_placeholder("Buscar ejercicio…").fill("Flex")
    page.get_by_role("button", name="Flexiones").click()
    expect(page.get_by_label("Carga (%)")).to_have_count(0)

    # Tested exercise → the field appears.
    page.get_by_role("button", name="Añadir ejercicio").click()
    page.get_by_placeholder("Buscar ejercicio…").fill("Peso")
    page.get_by_role("button", name="Peso muerto").click()
    expect(page.get_by_label("Carga (%)")).to_be_visible()


def test_detail_computes_load_kg_from_latest_test(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    create_strength_test_item: Callable[..., StrengthTestItem],
    create_strength_test_log: Callable[..., StrengthTestLog],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    deadlift = create_exercise(name="Peso muerto", type="gym")
    create_strength_test_item(exercise_id=deadlift.id, weight_multiplier=1.0)
    # Latest test result: 80 kg. A fractional 62.5% load → 50 kg.
    create_strength_test_log(athlete_id=member.id, results={deadlift.id: 80})
    training = _training_with(deadlift, create_training, load_percentage=62.5)
    log_in_as(member)

    page.goto(f"{app_url}/entrenamientos/{training.id}")
    main = page.get_by_role("main")
    expect(main.get_by_text("50 kg", exact=False)).to_be_visible()
    expect(main.get_by_text("(62.5%)", exact=False)).to_be_visible()


def test_detail_shows_percentage_and_warning_without_test(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    create_strength_test_item: Callable[..., StrengthTestItem],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    deadlift = create_exercise(name="Peso muerto", type="gym")
    create_strength_test_item(exercise_id=deadlift.id, weight_multiplier=1.0)
    # No test result for this athlete → percentage shown with a warning, no kg.
    training = _training_with(deadlift, create_training, load_percentage=70)
    log_in_as(member)

    page.goto(f"{app_url}/entrenamientos/{training.id}")
    main = page.get_by_role("main")
    expect(main.get_by_text("70%", exact=False)).to_be_visible()
    expect(main.get_by_text("kg", exact=False)).to_have_count(0)

    # The tooltip is hidden until the percentage is hovered, then it reveals.
    tooltip = main.get_by_role("tooltip").filter(has_text="Haz una prueba de fuerza")
    expect(tooltip).not_to_be_visible()
    main.get_by_label("Haz una prueba de fuerza para calcular una carga más precisa").hover()
    expect(tooltip).to_be_visible()
