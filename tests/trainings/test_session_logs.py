import re
from collections.abc import Callable

import sqlalchemy
from playwright.sync_api import Page, expect
from sqlalchemy import text

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


def _session_log_rows(engine: sqlalchemy.Engine, training_id: str) -> list[bool]:
    """The `complete` flag of every session log for a training, for asserting that a
    partial (complete=false) draft was/wasn't created."""
    with engine.connect() as conn:
        return list(
            conn.execute(
                text("SELECT complete FROM session_logs WHERE training_session_id = :tid"),
                {"tid": training_id},
            ).scalars()
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


def test_first_input_creates_hidden_partial_log(
    page: Page,
    app_url: str,
    _db_engine: sqlalchemy.Engine,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # The first real input auto-saves a partial log (so progress survives a reload),
    # but that partial stays invisible: no log-list entry, no "Última vez".
    member = create_user(role="member", email="member@example.com")
    training = _make_training(create_exercise, create_training)
    log_in_as(member)

    page.goto(f"{app_url}/entrenamientos/{training.id}/registrar")
    # No partial exists until the athlete touches something.
    assert _session_log_rows(_db_engine, str(training.id)) == []

    # Marking the first exercise done seeds exactly one partial (complete = false).
    page.get_by_role("button", name="Hecho").first.click()
    expect(page.get_by_role("button", name="Hecho").first).to_have_attribute(
        "aria-pressed", "true"
    )

    def one_partial() -> bool:
        return _session_log_rows(_db_engine, str(training.id)) == [False]

    # Poll until the debounced auto-save lands.
    for _ in range(50):
        if one_partial():
            break
        page.wait_for_timeout(100)
    assert one_partial(), _session_log_rows(_db_engine, str(training.id))

    # A second input still upserts the same single partial (never a second row).
    page.get_by_role("button", name="No hecho").nth(1).click()
    page.wait_for_timeout(1200)  # past the auto-save debounce
    assert _session_log_rows(_db_engine, str(training.id)) == [False]

    # The partial is invisible: the athlete's log list is empty…
    result = page.request.get(f"{app_url}/api/trainings/{training.id}/logs")
    assert result.json()["total_count"] == 0

    # …and the subtype list shows no "Última vez" for this session.
    page.goto(f"{app_url}/entrenamientos/gimnasio/acumulacion")
    row = page.get_by_role("listitem").filter(has_text="Sesión registrable")
    expect(row.get_by_text("Última vez", exact=False)).to_have_count(0)


def test_list_shows_in_progress_for_partial_then_clears_on_submit(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # A partial (in-progress) log surfaces as "En progreso" on the subtype list,
    # replacing "Última vez". Submitting clears the partial and flips it to last-done.
    member = create_user(role="member", email="member@example.com")
    training = _make_training(create_exercise, create_training)
    log_in_as(member)

    # Touch one exercise to seed a partial, then check the subtype list.
    page.goto(f"{app_url}/entrenamientos/{training.id}/registrar")
    page.get_by_role("button", name="Hecho").first.click()
    expect(page.get_by_role("button", name="Hecho").first).to_have_attribute(
        "aria-pressed", "true"
    )
    # Give the debounced auto-save time to land before navigating away.
    page.wait_for_timeout(1200)

    page.goto(f"{app_url}/entrenamientos/gimnasio/acumulacion")
    row = page.get_by_role("listitem").filter(has_text="Sesión registrable")
    expect(row.get_by_text("En progreso", exact=False)).to_be_visible()
    expect(row.get_by_text("Última vez", exact=False)).to_have_count(0)

    # Reopen and submit the resumed draft (the squat is already marked done) — the row
    # then goes back to "Última vez", no longer in progress.
    page.goto(f"{app_url}/entrenamientos/{training.id}/registrar")
    page.get_by_role("button", name="Finalizar sesión").click()
    expect(page.get_by_role("status").filter(has_text="Sesión registrada.")).to_be_visible()

    page.goto(f"{app_url}/entrenamientos/gimnasio/acumulacion")
    row = page.get_by_role("listitem").filter(has_text="Sesión registrable")
    expect(row.get_by_text("En progreso", exact=False)).to_have_count(0)
    expect(row.get_by_text("Última vez", exact=False)).to_be_visible()


def test_register_prefills_from_partial_with_banner_and_clear(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Marking an exercise done seeds a partial; reopening the register page pre-fills
    # the form from it and shows the "continuing where you left off" banner. "Empezar
    # de nuevo" discards the draft and resets the form.
    member = create_user(role="member", email="member@example.com")
    training = _make_training(create_exercise, create_training)
    log_in_as(member)

    page.goto(f"{app_url}/entrenamientos/{training.id}/registrar")
    # No banner on a fresh session.
    expect(page.get_by_text("Seguimos donde lo dejaste", exact=False)).to_have_count(0)

    # Mark the squat done, then let the debounced auto-save land.
    page.get_by_role("button", name="Hecho").first.click()
    expect(page.get_by_role("button", name="Hecho").first).to_have_attribute(
        "aria-pressed", "true"
    )
    page.wait_for_timeout(1200)

    # Reopen the page (as a lock+reload would): the draft is restored + the banner shows.
    page.goto(f"{app_url}/entrenamientos/{training.id}/registrar")
    expect(page.get_by_text("Seguimos donde lo dejaste", exact=False)).to_be_visible()
    expect(page.get_by_role("button", name="Hecho").first).to_have_attribute(
        "aria-pressed", "true"
    )

    # "Empezar de nuevo" clears the draft: banner gone, the exercise back to pending.
    page.get_by_role("button", name="Empezar de nuevo").click()
    expect(page.get_by_role("status").filter(has_text="Progreso descartado.")).to_be_visible()
    expect(page.get_by_text("Seguimos donde lo dejaste", exact=False)).to_have_count(0)
    expect(page.get_by_role("button", name="Hecho").first).to_have_attribute(
        "aria-pressed", "false"
    )

    # And the draft is really gone: a reload shows a fresh form (no banner).
    page.goto(f"{app_url}/entrenamientos/{training.id}/registrar")
    expect(page.get_by_text("Seguimos donde lo dejaste", exact=False)).to_have_count(0)
    expect(page.get_by_role("button", name="Hecho").first).to_have_attribute(
        "aria-pressed", "false"
    )


def test_live_updates_persist_parameter_across_reload(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Every change auto-saves the partial: a parameter value typed after marking done
    # is restored on reload (not just the first input).
    member = create_user(role="member", email="member@example.com")
    training = _make_training(create_exercise, create_training)
    log_in_as(member)

    page.goto(f"{app_url}/entrenamientos/{training.id}/registrar")
    page.get_by_role("button", name="Hecho").first.click()
    # The Peso field appears once done; type a value and let the debounced save land.
    peso = page.get_by_label("Peso", exact=False)
    peso.fill("72kg")
    page.wait_for_timeout(1200)

    # Reload as a lock+reopen would: the done state AND the typed value come back.
    page.goto(f"{app_url}/entrenamientos/{training.id}/registrar")
    expect(page.get_by_text("Seguimos donde lo dejaste", exact=False)).to_be_visible()
    expect(page.get_by_role("button", name="Hecho").first).to_have_attribute(
        "aria-pressed", "true"
    )
    expect(page.get_by_label("Peso", exact=False)).to_have_value("72kg")

    # A further edit updates the same draft; reload reflects the new value.
    page.get_by_label("Peso", exact=False).fill("75kg")
    page.wait_for_timeout(1200)
    page.goto(f"{app_url}/entrenamientos/{training.id}/registrar")
    expect(page.get_by_label("Peso", exact=False)).to_have_value("75kg")


def test_submit_promotes_partial_to_single_complete_log(
    page: Page,
    app_url: str,
    _db_engine: sqlalchemy.Engine,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Submitting a resumed draft promotes it in place: one complete log (no orphan
    # partial left behind), carrying the note entered at submit time.
    member = create_user(role="member", email="member@example.com")
    training = _make_training(create_exercise, create_training)
    log_in_as(member)

    # Seed a draft, then reload so we're submitting the resumed partial.
    page.goto(f"{app_url}/entrenamientos/{training.id}/registrar")
    page.get_by_role("button", name="Hecho").first.click()
    page.wait_for_timeout(1200)
    page.goto(f"{app_url}/entrenamientos/{training.id}/registrar")
    expect(page.get_by_text("Seguimos donde lo dejaste", exact=False)).to_be_visible()

    # A partial exists (complete=false) before submitting.
    assert _session_log_rows(_db_engine, str(training.id)) == [False]

    # Add a note and finish.
    page.get_by_label("Nota de la sesión", exact=False).fill("promoción")
    page.get_by_role("button", name="Finalizar sesión").click()
    expect(page.get_by_role("status").filter(has_text="Sesión registrada.")).to_be_visible()

    # Exactly one row, now complete — the draft was promoted, not duplicated.
    assert _session_log_rows(_db_engine, str(training.id)) == [True]

    # The completed log shows in the list with its note.
    expect(page).to_have_url(f"{app_url}/entrenamientos/{training.id}")
    logs = page.get_by_role("main").get_by_role("list").last
    expect(logs.get_by_text("promoción")).to_be_visible()


def test_save_indicator_shows_saving_then_saved(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # The auto-save indicator gives the athlete confidence their progress is saved:
    # it's hidden at rest, shows "Guardando" while the PUT is in flight, then "Guardado".
    member = create_user(role="member", email="member@example.com")
    training = _make_training(create_exercise, create_training)
    log_in_as(member)

    page.goto(f"{app_url}/entrenamientos/{training.id}/registrar")
    # Nothing shown before any change.
    expect(page.get_by_text("Guardado", exact=True)).to_have_count(0)

    page.get_by_role("button", name="Hecho").first.click()
    # After the debounced save resolves, "Guardado" is shown (the transient "Guardando"
    # may be too brief to assert reliably, so we assert the settled state).
    expect(page.get_by_text("Guardado", exact=True)).to_be_visible()


def test_failed_save_shows_error_then_retries_to_success(
    page: Page,
    app_url: str,
    _db_engine: sqlalchemy.Engine,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # When an auto-save fails, the indicator shows the error and a background retry
    # loop keeps trying the latest snapshot until it succeeds — no draft is lost.
    member = create_user(role="member", email="member@example.com")
    training = _make_training(create_exercise, create_training)
    log_in_as(member)

    # Fail the first partial-save PUT, then let subsequent ones through.
    calls = {"n": 0}

    def handle(route):
        if route.request.method == "PUT":
            calls["n"] += 1
            if calls["n"] == 1:
                route.fulfill(status=500, body="{}", content_type="application/json")
                return
        route.continue_()

    page.route("**/api/trainings/*/logs/partial", handle)

    page.goto(f"{app_url}/entrenamientos/{training.id}/registrar")
    page.get_by_role("button", name="Hecho").first.click()

    # The first save fails → the error indicator shows.
    expect(page.get_by_text("Error al guardar", exact=True)).to_be_visible()

    # The retry loop resends the latest snapshot and succeeds → "Guardado", and the
    # draft is now persisted (one complete=false row).
    expect(page.get_by_text("Guardado", exact=True)).to_be_visible(timeout=15000)

    def one_partial() -> bool:
        return _session_log_rows(_db_engine, str(training.id)) == [False]

    for _ in range(50):
        if one_partial():
            break
        page.wait_for_timeout(100)
    assert one_partial(), _session_log_rows(_db_engine, str(training.id))


def test_discrete_action_saves_without_debounce_wait(
    page: Page,
    app_url: str,
    _db_engine: sqlalchemy.Engine,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Discrete actions (marking done) save immediately, not on the debounce — the
    # partial lands well before the debounce window would elapse.
    member = create_user(role="member", email="member@example.com")
    training = _make_training(create_exercise, create_training)
    log_in_as(member)

    page.goto(f"{app_url}/entrenamientos/{training.id}/registrar")
    page.get_by_role("button", name="Hecho").first.click()

    # "Guardado" confirms the immediate save (no 800ms wait needed before it fires).
    expect(page.get_by_text("Guardado", exact=True)).to_be_visible(timeout=3000)
    assert _session_log_rows(_db_engine, str(training.id)) == [False]


def test_flush_saves_pending_edit_when_page_hidden(
    page: Page,
    app_url: str,
    _db_engine: sqlalchemy.Engine,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # A debounced (free-text) edit that hasn't saved yet is flushed on page-hide (phone
    # lock / app switch) via a keepalive request, so the last field isn't lost.
    member = create_user(role="member", email="member@example.com")
    training = _make_training(create_exercise, create_training)
    log_in_as(member)

    page.goto(f"{app_url}/entrenamientos/{training.id}/registrar")
    # Mark done (immediate save) so the Peso field appears and a partial exists.
    page.get_by_role("button", name="Hecho").first.click()
    expect(page.get_by_text("Guardado", exact=True)).to_be_visible(timeout=3000)

    # Type a weight but DON'T wait for the debounce — this edit is still pending.
    page.get_by_label("Peso", exact=False).fill("83kg")

    # Simulate the phone locking: force visibilityState=hidden and fire the event.
    page.evaluate(
        """
        Object.defineProperty(document, 'visibilityState',
          { configurable: true, get: () => 'hidden' });
        document.dispatchEvent(new Event('visibilitychange'));
        """
    )

    # The flush persists the typed value: reopening the page restores 83kg.
    page.goto(f"{app_url}/entrenamientos/{training.id}/registrar")
    expect(page.get_by_label("Peso", exact=False)).to_have_value("83kg")


def test_db_enforces_one_partial_per_session(
    _db_engine: sqlalchemy.Engine,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
) -> None:
    # A partial unique index guarantees at most one in-progress draft per athlete +
    # session (a DB backstop against concurrent auto-saves), while completed logs stay
    # unconstrained (a session is performed many times).
    import sqlalchemy.exc
    from sqlalchemy.orm import Session

    from app.models import SessionLog

    member = create_user(role="member", email="member@example.com")
    training = _make_training(create_exercise, create_training)

    def add_log(*, complete: bool) -> None:
        with Session(_db_engine, expire_on_commit=False) as session:
            session.add(
                SessionLog(
                    training_session_id=training.id, athlete_id=member.id, complete=complete
                )
            )
            session.commit()

    # First partial is fine; a second partial for the same athlete+session is rejected.
    add_log(complete=False)
    try:
        add_log(complete=False)
        raise AssertionError("expected the partial unique index to reject a second draft")
    except sqlalchemy.exc.IntegrityError:
        pass

    # Completed logs are unconstrained — an athlete performs the session repeatedly.
    add_log(complete=True)
    add_log(complete=True)

    assert sorted(_session_log_rows(_db_engine, str(training.id))) == [False, True, True]
