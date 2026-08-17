from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import (
    Exercise,
    LacticAcidPersonalBestLog,
    SpeedTestLog,
    TrainingBlock,
    TrainingItem,
    TrainingItemKind,
    TrainingSession,
    TrainingSubBlock,
    User,
)


def _pool_training_with(
    exercise: Exercise, create_training: Callable[..., TrainingSession], **fields: object
) -> TrainingSession:
    """A pool training with a single series item carrying the given item fields."""
    return create_training(
        title="Piscina",
        category="pool",
        subtype="endurance",
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
                                **fields,
                            )
                        ],
                    )
                ],
            )
        ],
    )


def test_target_time_field_only_for_pool_exercises(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    admin = create_user(role="admin", email="admin@example.com")
    create_exercise(name="Sentadilla", type="gym")
    create_exercise(name="Crol", type="pool")
    log_in_as(admin)

    # Gym builder: a gym exercise has no "Tiempo objetivo" field.
    page.goto(f"{app_url}/entrenamientos/gimnasio/acumulacion/nuevo")
    page.get_by_label("Título").fill("Sesión gym")
    page.get_by_role("button", name="Añadir bloque").click()
    page.get_by_label("Nombre del bloque").fill("Bloque")
    page.get_by_role("button", name="Añadir sub-bloque").click()
    page.get_by_label("Nombre del sub-bloque").fill("Sub")
    page.get_by_role("button", name="Añadir ejercicio").click()
    page.get_by_placeholder("Buscar ejercicio…").fill("Sent")
    page.get_by_role("button", name="Sentadilla").click()
    expect(page.get_by_label("Tiempo objetivo (fórmula)")).to_have_count(0)

    # Pool builder: the field appears for a pool exercise.
    page.goto(f"{app_url}/entrenamientos/piscina/resistencia/nuevo")
    page.get_by_label("Título").fill("Sesión piscina")
    page.get_by_role("button", name="Añadir bloque").click()
    page.get_by_label("Nombre del bloque").fill("Bloque")
    page.get_by_role("button", name="Añadir sub-bloque").click()
    page.get_by_label("Nombre del sub-bloque").fill("Sub")
    page.get_by_role("button", name="Añadir ejercicio").click()
    page.get_by_placeholder("Buscar ejercicio…").fill("Crol")
    page.get_by_role("button", name="Crol").click()
    expect(page.get_by_label("Tiempo objetivo (fórmula)")).to_be_visible()


def test_detail_computes_target_time_from_personal_best(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    create_lactic_acid_personal_best_log: Callable[..., LacticAcidPersonalBestLog],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    crol = create_exercise(name="Crol", type="pool")
    # Latest personal best: 26.5 s. Formula pb + 2 → 28.5 s.
    create_lactic_acid_personal_best_log(athlete_id=member.id, seconds=26.5)
    training = _pool_training_with(crol, create_training, target_time_formula="pb + 2")
    log_in_as(member)

    page.goto(f"{app_url}/entrenamientos/{training.id}")
    main = page.get_by_role("main")
    expect(main.get_by_text("28.5 s", exact=False)).to_be_visible()
    expect(main.get_by_text("(pb + 2)", exact=False)).to_be_visible()

    # Hovering the computed time reveals a note citing the personal best it came from.
    note = main.get_by_role("tooltip").filter(has_text="última marca personal")
    expect(note).not_to_be_visible()
    main.get_by_label("Calculado a partir de tu última marca personal").hover()
    expect(note).to_be_visible()


def test_detail_shows_formula_and_warning_without_personal_best(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    crol = create_exercise(name="Crol", type="pool")
    # No personal best for this athlete → the formula is shown with a warning, no time.
    training = _pool_training_with(crol, create_training, target_time_formula="pb + 2")
    log_in_as(member)

    page.goto(f"{app_url}/entrenamientos/{training.id}")
    main = page.get_by_role("main")
    expect(main.get_by_text("Tiempo objetivo:", exact=False)).to_be_visible()
    expect(main.get_by_text("pb + 2", exact=False)).to_be_visible()
    # No computed time: the "calculated from your personal best" tooltip isn't rendered.
    expect(main.get_by_label("Calculado a partir de tu última marca personal")).to_have_count(0)

    tooltip = main.get_by_role("tooltip").filter(has_text="Haz una prueba de ácido láctico")
    expect(tooltip).not_to_be_visible()
    main.get_by_label("Haz una prueba de ácido láctico para calcular el tiempo objetivo").hover()
    expect(tooltip).to_be_visible()


def test_register_computes_target_time_from_personal_best(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    create_lactic_acid_personal_best_log: Callable[..., LacticAcidPersonalBestLog],
    log_in_as: Callable[[User], None],
) -> None:
    # The target time also shows when logging a session (not just on the detail page).
    member = create_user(role="member", email="member@example.com")
    crol = create_exercise(name="Crol", type="pool")
    create_lactic_acid_personal_best_log(athlete_id=member.id, seconds=26.5)
    training = _pool_training_with(crol, create_training, target_time_formula="pb + 2")
    log_in_as(member)

    page.goto(f"{app_url}/entrenamientos/{training.id}/registrar")
    main = page.get_by_role("main")
    expect(main.get_by_text("28.5 s", exact=False)).to_be_visible()
    expect(main.get_by_text("(pb + 2)", exact=False)).to_be_visible()


def test_detail_computes_target_time_from_speed_test(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    create_speed_test_log: Callable[..., SpeedTestLog],
    log_in_as: Callable[[User], None],
) -> None:
    # An `st` formula computes from the latest speed-test result, and the messaging
    # refers to the speed test (not the lactic personal best).
    member = create_user(role="member", email="member@example.com")
    crol = create_exercise(name="Crol", type="pool")
    # Latest speed-test result: 12 s. Formula st * 2 → 24 s.
    create_speed_test_log(athlete_id=member.id, seconds=12)
    training = _pool_training_with(crol, create_training, target_time_formula="st * 2")
    log_in_as(member)

    page.goto(f"{app_url}/entrenamientos/{training.id}")
    main = page.get_by_role("main")
    expect(main.get_by_text("24 s", exact=False)).to_be_visible()
    expect(main.get_by_text("(st * 2)", exact=False)).to_be_visible()

    note = main.get_by_role("tooltip").filter(has_text="resultado de velocidad")
    expect(note).not_to_be_visible()
    main.get_by_label("Calculado a partir de tu último resultado de velocidad").hover()
    expect(note).to_be_visible()


def test_detail_st_formula_warns_to_take_speed_test(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    create_lactic_acid_personal_best_log: Callable[..., LacticAcidPersonalBestLog],
    log_in_as: Callable[[User], None],
) -> None:
    # An `st` formula with no speed-test result warns to take the SPEED test — even when
    # a lactic personal best exists (the messaging follows the formula's variable).
    member = create_user(role="member", email="member@example.com")
    crol = create_exercise(name="Crol", type="pool")
    create_lactic_acid_personal_best_log(athlete_id=member.id, seconds=26.5)
    training = _pool_training_with(crol, create_training, target_time_formula="st * 2")
    log_in_as(member)

    page.goto(f"{app_url}/entrenamientos/{training.id}")
    main = page.get_by_role("main")
    expect(main.get_by_text("st * 2", exact=False)).to_be_visible()
    tooltip = main.get_by_role("tooltip").filter(has_text="Haz una prueba de velocidad")
    expect(tooltip).not_to_be_visible()
    main.get_by_label("Haz una prueba de velocidad para calcular el tiempo objetivo").hover()
    expect(tooltip).to_be_visible()
