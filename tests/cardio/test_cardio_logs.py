from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import (
    CardioTraining,
    User,
    Week,
    WeekRequirement,
)


def _week(
    create_week: Callable[..., Week], name: str, category: str, subtype: str, count: int = 2
) -> Week:
    return create_week(
        name=name,
        phase="accumulation",
        requirements=[
            WeekRequirement(position=0, category=category, subtype=subtype, count=count)
        ],
    )


def test_log_cardio_session_with_activity_and_note(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_cardio_training: Callable[..., CardioTraining],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    training = create_cardio_training(title="Aeróbico", subtype="aerobic")
    log_in_as(member)

    # Start from the detail page's "Empezar" button.
    page.goto(f"{app_url}/entrenamientos/cardio/sesion/{training.id}")
    page.get_by_role("link", name="Empezar").click()
    page.wait_for_url("**/registrar")

    page.get_by_label("Actividad", exact=False).fill("Carrera")
    page.get_by_label("Nota de la sesión", exact=False).fill("5km suaves")
    page.get_by_role("button", name="Finalizar sesión").click()
    expect(page.get_by_role("status").filter(has_text="Sesión registrada.")).to_be_visible()

    # The log shows up in the session's log list (activity · note). Reload so the
    # list refetches: we viewed the detail before registering, so an in-app return
    # would serve SWR's still-deduped empty cache.
    page.wait_for_url(f"**/cardio/sesion/{training.id}")
    page.reload()
    log_row = page.get_by_role("link", name="Carrera", exact=False)
    expect(log_row).to_be_visible()

    # Opening it shows the activity and note.
    log_row.click()
    page.wait_for_url("**/registros/**")
    expect(page.get_by_text("Carrera")).to_be_visible()
    expect(page.get_by_text("5km suaves")).to_be_visible()


def test_register_offers_only_matching_weeks(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_cardio_training: Callable[..., CardioTraining],
    create_week: Callable[..., Week],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    training = create_cardio_training(title="Aeróbico", subtype="aerobic")
    _week(create_week, "Semana cardio", "cardio", "aerobic")
    _week(create_week, "Semana pool", "pool", "endurance")
    log_in_as(member)

    page.goto(f"{app_url}/entrenamientos/cardio/sesion/{training.id}/registrar")
    weeks = page.get_by_label("Semana", exact=True)
    expect(weeks.get_by_role("option", name="Semana cardio")).to_be_attached()
    # The pool week doesn't recommend this cardio/aerobic training.
    expect(weeks.get_by_role("option", name="Semana pool")).to_have_count(0)


def test_cardio_log_counts_toward_week_progress(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_cardio_training: Callable[..., CardioTraining],
    create_week: Callable[..., Week],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    training = create_cardio_training(title="Aeróbico", subtype="aerobic")
    # A week needing 1 cardio/aerobic session — one log fills it.
    week = _week(create_week, "Semana llena", "cardio", "aerobic", count=1)
    log_in_as(member)

    # Log it, linking to the week.
    page.goto(f"{app_url}/entrenamientos/cardio/sesion/{training.id}/registrar")
    page.get_by_label("Actividad", exact=False).fill("Remo")
    page.get_by_label("Semana", exact=True).select_option(label="Semana llena")
    page.get_by_role("button", name="Finalizar sesión").click()
    expect(page.get_by_role("status").filter(has_text="Sesión registrada.")).to_be_visible()

    # The week now shows the requirement as complete (1/1) and lists the cardio log,
    # which links back to the cardio log detail page.
    page.goto(f"{app_url}/calendario/{week.id}")
    expect(page.get_by_text("1/1")).to_be_visible()
    # The log row links to the cardio log detail (distinguished from the requirement
    # link by its /registros/ href).
    log_link = page.locator(f"a[href*='/cardio/sesion/{training.id}/registros/']")
    expect(log_link).to_be_visible()
    log_link.click()
    page.wait_for_url(f"**/cardio/sesion/{training.id}/registros/**")
    expect(page.get_by_text("Remo")).to_be_visible()


def test_completed_week_drops_from_register_but_stays_on_detail(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_cardio_training: Callable[..., CardioTraining],
    create_week: Callable[..., Week],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    training = create_cardio_training(title="Aeróbico", subtype="aerobic")
    # Only one recommending week, needing 1 — one log fills it.
    _week(create_week, "Semana llena", "cardio", "aerobic", count=1)
    log_in_as(member)

    # Log it into "Semana llena" → that week is now complete.
    page.goto(f"{app_url}/entrenamientos/cardio/sesion/{training.id}/registrar")
    page.get_by_label("Actividad", exact=False).fill("Bici")
    page.get_by_label("Semana", exact=True).select_option(label="Semana llena")
    page.get_by_role("button", name="Finalizar sesión").click()
    expect(page.get_by_role("status").filter(has_text="Sesión registrada.")).to_be_visible()

    # Registering again no longer offers the full week (no week select at all here).
    page.goto(f"{app_url}/entrenamientos/cardio/sesion/{training.id}/registrar")
    expect(page.get_by_label("Semana", exact=True)).to_have_count(0)

    # But the existing log keeps it selectable, so the link can still be edited.
    page.goto(f"{app_url}/entrenamientos/cardio/sesion/{training.id}")
    page.get_by_role("link", name="Bici", exact=False).click()
    page.wait_for_url("**/registros/**")
    week = page.get_by_label("Semana", exact=True)
    expect(week).to_contain_text("Semana llena")
