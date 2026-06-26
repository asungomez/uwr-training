import re
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
    """A gym training with a squat (one 'Peso' param + one alternative, which also
    tracks 'Peso') and a plank."""
    alt = create_exercise(
        name="Zancada", type="gym", parameters=[ExerciseParameter(name="Peso")]
    )
    squat = create_exercise(
        name="Sentadilla",
        type="gym",
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
                            ),
                            TrainingItem(
                                kind=TrainingItemKind.series, position=1, exercise_id=plank.id
                            ),
                        ],
                    )
                ],
            )
        ],
    )


def _register_a_session(page: Page, app_url: str, training_id: str) -> None:
    """Go through the register flow: squat done as its alternative with Peso=80,
    plank skipped, with a note."""
    page.goto(f"{app_url}/entrenamientos/{training_id}/registrar")
    page.get_by_role("button", name="Cambiar a ejercicio alternativo").click()
    page.get_by_role("button", name="Hecho").first.click()
    page.get_by_label("Peso", exact=False).fill("80kg")
    page.get_by_role("button", name="No hecho").nth(1).click()
    page.get_by_label("Nota de la sesión", exact=False).fill("buena sesión")
    page.get_by_role("button", name="Finalizar sesión").click()
    expect(page.get_by_role("status").filter(has_text="Sesión registrada.")).to_be_visible()


def test_list_shows_last_done_after_logging(
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

    # Before logging, the subtype list row shows no "Última vez".
    page.goto(f"{app_url}/entrenamientos/gimnasio/acumulacion")
    row = page.get_by_role("listitem").filter(has_text="Sesión registrable")
    expect(row).to_be_visible()
    expect(row.get_by_text("Última vez", exact=False)).to_have_count(0)

    # After logging it, the row shows when it was last done.
    _register_a_session(page, app_url, str(training.id))
    page.goto(f"{app_url}/entrenamientos/gimnasio/acumulacion")
    row = page.get_by_role("listitem").filter(has_text="Sesión registrable")
    expect(row.get_by_text("Última vez", exact=False)).to_be_visible()


def test_detail_shows_no_logs_initially(
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

    main = page.get_by_role("main")
    expect(main.get_by_role("heading", name="Tus registros")).to_be_visible()
    expect(main.get_by_text("Todavía no has registrado esta sesión.")).to_be_visible()


def test_logged_session_appears_in_list(
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
    _register_a_session(page, app_url, str(training.id))

    # Back on the detail page, the log shows in "Tus registros" with its note.
    expect(page).to_have_url(f"{app_url}/entrenamientos/{training.id}")
    logs = page.get_by_role("main").get_by_role("list").last
    expect(logs.get_by_text("buena sesión")).to_be_visible()


def test_open_log_detail_shows_done_skipped_and_params(
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
    _register_a_session(page, app_url, str(training.id))

    # Open the log from the list.
    page.get_by_role("link", name="buena sesión").click()
    expect(page).to_have_url(re.compile(r"/registros/[0-9a-f-]+$"))

    main = page.get_by_role("main")
    expect(main.get_by_text("buena sesión")).to_be_visible()
    # Squat: done, performed as its alternative, with the Peso value.
    expect(main.get_by_text("Zancada")).to_be_visible()
    expect(main.get_by_text("alternativa de Sentadilla", exact=False)).to_be_visible()
    expect(main.get_by_text("Peso:", exact=False)).to_be_visible()
    expect(main.get_by_text("80kg")).to_be_visible()
    # Plank: skipped.
    expect(main.get_by_text("Plancha")).to_be_visible()
    expect(main.get_by_text("No hecho")).to_be_visible()
    expect(main.get_by_text("Hecho", exact=True)).to_be_visible()


def test_member_cannot_open_another_athletes_log(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # One athlete logs a session.
    author = create_user(role="member", email="author@example.com")
    training = _make_training(create_exercise, create_training)
    log_in_as(author)
    _register_a_session(page, app_url, str(training.id))
    page.get_by_role("link", name="buena sesión").click()
    expect(page).to_have_url(re.compile(r"/registros/[0-9a-f-]+$"))
    log_url = page.url

    # A different athlete can't see it (scoped to the owner → not found).
    other = create_user(role="member", email="other@example.com")
    log_in_as(other)
    page.goto(log_url)
    expect(page.get_by_text("No se ha encontrado el registro.")).to_be_visible()
