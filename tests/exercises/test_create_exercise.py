from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import User


def _open_new_exercise_form(page: Page, app_url: str) -> None:
    page.goto(f"{app_url}/ejercicios")
    page.get_by_role("link", name="Nuevo ejercicio").click()


def test_admin_creates_exercise(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a logged-in admin on the new-exercise page.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    _open_new_exercise_form(page, app_url)

    # When they fill the form and submit. Description is a WYSIWYG editor
    # (textbox 0 = name input, textbox 1 = the markdown editor).
    page.get_by_label("Nombre").fill("Sentadilla")
    editor = page.get_by_role("textbox").nth(1)
    editor.click()
    editor.type("Trabajo de piernas")
    page.get_by_label("Tipo", exact=True).select_option(label="Gimnasio")
    page.get_by_role("button", name="Guardar ejercicio").click()

    # Then a success toast confirms it and we land on the new exercise's detail page.
    expect(page.get_by_role("status").filter(has_text="Ejercicio creado.")).to_be_visible()
    expect(page.get_by_role("heading", name="Sentadilla")).to_be_visible()


def test_duplicate_exercise_shows_spanish_error(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., object],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an exercise already exists.
    admin = create_user(role="admin", email="admin@example.com")
    create_exercise(name="Apnea", type="pool")
    log_in_as(admin)

    # When I try to create another with the same name.
    _open_new_exercise_form(page, app_url)
    page.get_by_label("Nombre").fill("Apnea")
    page.get_by_label("Tipo", exact=True).select_option(label="Piscina")
    page.get_by_role("button", name="Guardar ejercicio").click()

    # Then the form shows the localized duplicate error.
    expect(page.get_by_role("alert")).to_have_text("Ya existe un ejercicio con este nombre.")


def test_name_required_blocks_submit(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given the new-exercise form.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    _open_new_exercise_form(page, app_url)

    # When I submit without a name.
    page.get_by_role("button", name="Guardar ejercicio").click()

    # Then client-side validation flags it.
    expect(page.get_by_text("El nombre es obligatorio")).to_be_visible()
