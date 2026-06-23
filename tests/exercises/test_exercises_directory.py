from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import User


def _create_exercise(page: Page, app_url: str, name: str, type_label: str) -> None:
    page.goto(f"{app_url}/ejercicios")
    page.get_by_role("button", name="Nuevo ejercicio").click()
    page.get_by_label("Nombre").fill(name)
    page.get_by_label("Tipo", exact=True).select_option(label=type_label)
    page.get_by_role("button", name="Guardar ejercicio").click()
    expect(page.get_by_role("status").filter(has_text="Ejercicio creado.")).to_be_visible()


def test_created_exercise_appears_as_card(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a logged-in admin.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)

    # When they create an exercise.
    _create_exercise(page, app_url, "Sentadilla", "Gimnasio")

    # Then it shows up live as a card (no reload).
    expect(page.get_by_role("heading", name="Sentadilla")).to_be_visible()


def test_filter_by_type(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a gym and a pool exercise.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    _create_exercise(page, app_url, "Press banca", "Gimnasio")
    _create_exercise(page, app_url, "Apnea", "Piscina")

    # When I filter by Piscina.
    page.get_by_label("Filtrar por tipo").select_option(label="Piscina")

    # Then only the pool exercise remains.
    expect(page.get_by_role("heading", name="Apnea")).to_be_visible()
    expect(page.get_by_role("heading", name="Press banca")).not_to_be_visible()


def test_search_by_name(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given two exercises.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    _create_exercise(page, app_url, "Dominadas", "Gimnasio")
    _create_exercise(page, app_url, "Buceo", "Piscina")

    # When I search by a partial name.
    page.get_by_label("Buscar").fill("domi")

    # Then only the match shows.
    expect(page.get_by_role("heading", name="Dominadas")).to_be_visible()
    expect(page.get_by_role("heading", name="Buceo")).not_to_be_visible()
