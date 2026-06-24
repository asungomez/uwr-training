from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import Exercise, User


def test_admin_edits_exercise(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an existing exercise.
    admin = create_user(role="admin", email="admin@example.com")
    create_exercise(name="Sentadilla", description="Piernas", type="gym")
    log_in_as(admin)
    page.goto(f"{app_url}/ejercicios")

    # When the admin opens the edit page (the form is pre-populated).
    page.get_by_role("link", name="Editar Sentadilla").click()
    name = page.get_by_label("Nombre")
    expect(name).to_have_value("Sentadilla")
    # Description is a WYSIWYG editor (contenteditable), pre-loaded with the markdown.
    expect(page.get_by_role("textbox").nth(1)).to_contain_text("Piernas")
    name.fill("Sentadilla búlgara")
    page.get_by_label("Tipo", exact=True).select_option(label="Piscina")
    page.get_by_role("button", name="Guardar ejercicio").click()

    # Then a toast confirms it and the detail page reflects the new name.
    expect(page.get_by_role("status").filter(has_text="Ejercicio actualizado.")).to_be_visible()
    expect(page.get_by_role("heading", name="Sentadilla búlgara")).to_be_visible()


def test_edit_duplicate_name_shows_spanish_error(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # Given two exercises.
    admin = create_user(role="admin", email="admin@example.com")
    create_exercise(name="Press banca", type="gym")
    create_exercise(name="Dominadas", type="gym")
    log_in_as(admin)
    page.goto(f"{app_url}/ejercicios")

    # When I rename one to clash with the other.
    page.get_by_role("link", name="Editar Dominadas").click()
    page.get_by_label("Nombre").fill("Press banca")
    page.get_by_role("button", name="Guardar ejercicio").click()

    # Then the form shows the localized duplicate error.
    expect(page.get_by_role("alert")).to_have_text("Ya existe un ejercicio con este nombre.")


def test_admin_deletes_exercise(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an existing exercise.
    admin = create_user(role="admin", email="admin@example.com")
    create_exercise(name="Apnea", type="pool")
    log_in_as(admin)
    page.goto(f"{app_url}/ejercicios")

    # When the admin deletes it and confirms.
    page.get_by_role("button", name="Eliminar Apnea").click()
    dialog = page.get_by_role("dialog", name="Eliminar ejercicio")
    expect(dialog).to_be_visible()
    dialog.get_by_role("button", name="Eliminar").click()

    # Then a toast confirms it and the card disappears.
    expect(page.get_by_role("status").filter(has_text="Ejercicio eliminado.")).to_be_visible()
    expect(page.get_by_role("heading", name="Apnea")).not_to_be_visible()


def test_delete_can_be_cancelled(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an existing exercise.
    admin = create_user(role="admin", email="admin@example.com")
    create_exercise(name="Buceo", type="pool")
    log_in_as(admin)
    page.goto(f"{app_url}/ejercicios")

    # When the admin opens the delete dialog but cancels.
    page.get_by_role("button", name="Eliminar Buceo").click()
    page.get_by_role("button", name="Cancelar").click()

    # Then the exercise is still there.
    expect(page.get_by_role("dialog")).not_to_be_visible()
    expect(page.get_by_role("heading", name="Buceo")).to_be_visible()


def test_member_sees_no_edit_or_delete(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an existing exercise.
    create_exercise(name="Zancadas", type="gym")

    # When a member views the exercises page.
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)
    page.goto(f"{app_url}/ejercicios")
    expect(page.get_by_role("heading", name="Zancadas")).to_be_visible()

    # Then no edit/delete controls are shown.
    expect(page.get_by_role("link", name="Editar Zancadas")).not_to_be_visible()
    expect(page.get_by_role("button", name="Eliminar Zancadas")).not_to_be_visible()
