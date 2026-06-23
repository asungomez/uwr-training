from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import User


def _open_new_exercise_modal(page: Page, app_url: str) -> None:
    page.goto(f"{app_url}/ejercicios")
    page.get_by_role("button", name="Nuevo ejercicio").click()


def test_admin_creates_exercise(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a logged-in admin on the exercises page.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    _open_new_exercise_modal(page, app_url)

    # When they fill the form and submit.
    page.get_by_label("Nombre").fill("Sentadilla")
    page.get_by_label("Descripción").fill("Trabajo de piernas")
    page.get_by_label("Tipo").select_option(label="Gimnasio")
    page.get_by_role("button", name="Crear ejercicio").click()

    # Then a success toast confirms it and the modal closes.
    expect(page.get_by_role("status").filter(has_text="Ejercicio creado.")).to_be_visible()
    expect(page.get_by_role("button", name="Crear ejercicio")).not_to_be_visible()


def test_duplicate_exercise_shows_spanish_error(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an exercise already exists.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    _open_new_exercise_modal(page, app_url)
    page.get_by_label("Nombre").fill("Apnea")
    page.get_by_label("Tipo").select_option(label="Piscina")
    page.get_by_role("button", name="Crear ejercicio").click()
    expect(page.get_by_role("status").filter(has_text="Ejercicio creado.")).to_be_visible()

    # When I try to create another with the same name.
    _open_new_exercise_modal(page, app_url)
    page.get_by_label("Nombre").fill("Apnea")
    page.get_by_label("Tipo").select_option(label="Piscina")
    page.get_by_role("button", name="Crear ejercicio").click()

    # Then the modal shows the localized duplicate error.
    expect(page.get_by_role("alert")).to_have_text("Ya existe un ejercicio con este nombre.")


def test_name_required_blocks_submit(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given the new-exercise modal is open.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    _open_new_exercise_modal(page, app_url)

    # When I submit without a name.
    page.get_by_role("button", name="Crear ejercicio").click()

    # Then client-side validation flags it.
    expect(page.get_by_text("El nombre es obligatorio")).to_be_visible()
