from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import BodyweightLog, User


def test_sidebar_has_pruebas_section(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos")

    nav = page.get_by_role("navigation").first
    expect(nav.get_by_text("Pruebas", exact=True)).to_be_visible()
    # "Prueba de fuerza" is a real link; "Prueba de velocidad" isn't (no destination yet).
    expect(nav.get_by_role("link", name="Prueba de fuerza")).to_be_visible()
    expect(nav.get_by_role("link", name="Prueba de velocidad")).to_have_count(0)
    expect(nav.get_by_text("Prueba de velocidad", exact=True)).to_be_visible()


def test_strength_test_link_opens_explanation(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos")

    page.get_by_role("link", name="Prueba de fuerza").click()
    expect(page).to_have_url(f"{app_url}/pruebas/fuerza")

    main = page.get_by_role("main")
    expect(main.get_by_role("heading", name="Prueba de fuerza")).to_be_visible()
    expect(main.get_by_text("guiar el esfuerzo necesario", exact=False)).to_be_visible()
    expect(main.get_by_text("último peso corporal registrado", exact=False)).to_be_visible()


def test_register_warns_when_no_bodyweight(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)

    page.goto(f"{app_url}/pruebas/fuerza")
    page.get_by_role("link", name="Hacer prueba").click()
    expect(page).to_have_url(f"{app_url}/pruebas/fuerza/registrar")

    # No body-weight register → a warning, no reference weight, and a shortcut to register.
    main = page.get_by_role("main")
    expect(main.get_by_text("al menos un registro de peso", exact=False)).to_be_visible()
    expect(main.get_by_role("link", name="Registrar peso")).to_be_visible()
    expect(main.get_by_text("Peso corporal de referencia", exact=False)).to_have_count(0)


def test_register_shows_reference_bodyweight(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_bodyweight_log: Callable[..., BodyweightLog],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    create_bodyweight_log(athlete_id=member.id, weight_kg=72.5)
    log_in_as(member)

    page.goto(f"{app_url}/pruebas/fuerza/registrar")
    main = page.get_by_role("main")
    # With a body weight (but no exercises configured here), the reference weight shows
    # and there's no missing-bodyweight warning. The populated form is covered in
    # test_strength_test_log.py.
    expect(main.get_by_text("72.5 kg", exact=False)).to_be_visible()
    expect(main.get_by_text("todavía no tiene ejercicios", exact=False)).to_be_visible()
    expect(main.get_by_text("al menos un registro de peso", exact=False)).to_have_count(0)
