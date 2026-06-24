from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import (
    Exercise,
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


def _go_to_new_form_with_sub_block(page: Page, app_url: str) -> None:
    # Category + subtype come from the URL now, not form fields.
    page.goto(f"{app_url}/entrenamientos/gimnasio/acumulacion/nuevo")
    page.get_by_label("Título").fill("Sesión con ejercicios")
    page.get_by_role("button", name="Añadir bloque").click()
    page.get_by_label("Nombre del bloque").fill("Bloque")
    page.get_by_role("button", name="Añadir sub-bloque").click()
    page.get_by_label("Nombre del sub-bloque").fill("Sub")


def test_admin_adds_exercise_series_when_creating(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an exercise to pick and a new training with a sub-block.
    admin = create_user(role="admin", email="admin@example.com")
    create_exercise(name="Sentadilla", type="gym")
    log_in_as(admin)
    _go_to_new_form_with_sub_block(page, app_url)

    # When I add an exercise series, search and pick the exercise, then fill the
    # prescription (leaving distance blank to confirm it's optional).
    page.get_by_role("button", name="Añadir ejercicio").click()
    page.get_by_placeholder("Buscar ejercicio…").fill("Sent")
    page.get_by_role("button", name="Sentadilla").click()
    page.get_by_label("Series").fill("4")
    page.get_by_label("Repeticiones por serie").fill("8")
    page.get_by_label("Tiempo por serie").fill("1:30")
    page.get_by_label("Intensidad").fill("RPE 7")
    page.get_by_label("Notas del ejercicio").fill("controla la bajada")
    page.get_by_role("button", name="Crear entrenamiento").click()

    # Then the detail page shows the exercise with only its populated fields.
    expect(page.get_by_role("status").filter(has_text="Entrenamiento creado.")).to_be_visible()
    main = page.get_by_role("main")
    expect(main.get_by_text("Sentadilla")).to_be_visible()
    expect(main.get_by_text("Series: 4")).to_be_visible()
    expect(main.get_by_text("Reps/serie: 8")).to_be_visible()
    expect(main.get_by_text("Tiempo por serie: 1:30")).to_be_visible()
    expect(main.get_by_text("Intensidad: RPE 7")).to_be_visible()
    expect(main.get_by_text("controla la bajada")).to_be_visible()
    # Distance was left blank, so it isn't shown.
    expect(main.get_by_text("Distancia:")).to_have_count(0)


def test_exercise_search_is_filtered_by_training_category(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a gym and a pool exercise.
    admin = create_user(role="admin", email="admin@example.com")
    create_exercise(name="Sentadilla gimnasio", type="gym")
    create_exercise(name="Sentadilla piscina", type="pool")
    log_in_as(admin)

    # When the training is for gym, the picker offers only the gym exercise.
    _go_to_new_form_with_sub_block(page, app_url)
    page.get_by_role("button", name="Añadir ejercicio").click()
    page.get_by_placeholder("Buscar ejercicio…").fill("Sentadilla")
    expect(page.get_by_role("button", name="Sentadilla gimnasio")).to_be_visible()
    expect(page.get_by_role("button", name="Sentadilla piscina")).to_have_count(0)


def test_series_requires_an_exercise(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a new training with an exercise series added but no exercise chosen.
    admin = create_user(role="admin", email="admin@example.com")
    create_exercise(name="Sentadilla", type="gym")
    log_in_as(admin)
    _go_to_new_form_with_sub_block(page, app_url)
    page.get_by_role("button", name="Añadir ejercicio").click()

    # When I submit, client-side validation blocks it: no success toast, still on
    # the form with the (unpicked) exercise search showing.
    page.get_by_role("button", name="Crear entrenamiento").click()
    expect(page.get_by_role("status").filter(has_text="Entrenamiento creado.")).to_have_count(0)
    expect(page.get_by_placeholder("Buscar ejercicio…")).to_be_visible()
    expect(page.get_by_role("button", name="Crear entrenamiento")).to_be_visible()


def test_edit_prefills_series_and_persists_changes(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a sub-block with one exercise series.
    admin = create_user(role="admin", email="admin@example.com")
    exercise = create_exercise(name="Press banca", type="gym")
    training = create_training(
        title="Editable",
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
                            _series(
                                exercise,
                                0,
                                sets=3,
                                reps=10,
                                duration_seconds=120,
                                effort="RPE 8",
                                text="pausa abajo",
                            )
                        ],
                    )
                ],
            )
        ],
    )
    log_in_as(admin)
    page.goto(f"{app_url}/entrenamientos/{training.id}/editar")

    # The existing series is pre-filled (time shown as mm:ss).
    expect(page.get_by_text("Press banca")).to_be_visible()
    expect(page.get_by_label("Series")).to_have_value("3")
    expect(page.get_by_label("Repeticiones por serie")).to_have_value("10")
    expect(page.get_by_label("Tiempo por serie")).to_have_value("2:00")
    expect(page.get_by_label("Intensidad")).to_have_value("RPE 8")
    expect(page.get_by_label("Notas del ejercicio")).to_have_value("pausa abajo")

    # When I bump the sets and save.
    page.get_by_label("Series").fill("5")
    page.get_by_role("button", name="Guardar cambios").click()
    expect(page.get_by_role("status").filter(has_text="Entrenamiento actualizado.")).to_be_visible()

    # Then the change round-trips after reload.
    page.goto(f"{app_url}/entrenamientos/{training.id}/editar")
    expect(page.get_by_label("Series")).to_have_value("5")


def test_member_sees_only_populated_series_fields_on_detail(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a series with only sets + distance filled in.
    member = create_user(role="member", email="member@example.com")
    exercise = create_exercise(name="Nado", type="pool")
    training = create_training(
        title="Solo distancia",
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
                        items=[_series(exercise, 0, sets=2, distance_meters=400)],
                    )
                ],
            )
        ],
    )
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos/{training.id}")

    # Then only the populated fields show.
    main = page.get_by_role("main")
    expect(main.get_by_text("Nado")).to_be_visible()
    expect(main.get_by_text("Series: 2")).to_be_visible()
    expect(main.get_by_text("Distancia: 400 m")).to_be_visible()
    expect(main.get_by_text("Reps/serie:")).to_have_count(0)
    expect(main.get_by_text("Tiempo por serie:")).to_have_count(0)
    expect(main.get_by_text("Intensidad:")).to_have_count(0)
