from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import TrainingSession, User


def test_admin_edits_training_from_detail(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an existing training.
    admin = create_user(role="admin", email="admin@example.com")
    training = create_training(title="Original", category="gym", subtype="accumulation")
    log_in_as(admin)
    page.goto(f"{app_url}/entrenamientos/{training.id}")

    # When the admin opens the edit page (pre-filled) and changes the title.
    page.get_by_role("link", name="Editar").click()
    expect(page).to_have_url(f"{app_url}/entrenamientos/{training.id}/editar")
    expect(page.get_by_label("Título")).to_have_value("Original")
    # Category and subtype are immutable: shown in the heading, not as editable fields.
    expect(page.get_by_role("heading", name="Gimnasio / Acumulación")).to_be_visible()
    expect(page.get_by_label("Categoría")).to_have_count(0)
    expect(page.get_by_label("Subtipo")).to_have_count(0)

    page.get_by_label("Título").fill("Editado")
    page.get_by_role("button", name="Guardar cambios").click()

    # Then a toast confirms it and the detail page reflects the new title while the
    # scope is unchanged (badges are spans — scope away from the breadcrumb links).
    expect(page.get_by_role("status").filter(has_text="Entrenamiento actualizado.")).to_be_visible()
    expect(page).to_have_url(f"{app_url}/entrenamientos/{training.id}")
    main = page.get_by_role("main")
    expect(main.get_by_role("heading", name="Editado")).to_be_visible()
    expect(main.locator("span").get_by_text("Gimnasio")).to_be_visible()
    expect(main.locator("span").get_by_text("Acumulación")).to_be_visible()


def test_member_cannot_access_edit_page(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a member and an existing training.
    member = create_user(role="member", email="member@example.com")
    training = create_training(title="Original", category="gym", subtype="accumulation")
    log_in_as(member)

    # When they hit the edit URL directly, the admin guard redirects them away.
    page.goto(f"{app_url}/entrenamientos/{training.id}/editar")
    expect(page.get_by_role("button", name="Guardar cambios")).not_to_be_visible()
    expect(page).to_have_url(f"{app_url}/entrenamientos")


def test_member_does_not_see_edit_or_delete_on_detail(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a member viewing a training.
    member = create_user(role="member", email="member@example.com")
    training = create_training(title="Solo lectura", category="gym", subtype="accumulation")
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos/{training.id}")

    # Then no admin controls are shown.
    expect(page.get_by_role("heading", name="Solo lectura")).to_be_visible()
    expect(page.get_by_role("link", name="Editar")).not_to_be_visible()
    expect(page.get_by_role("button", name="Eliminar")).not_to_be_visible()


def test_admin_deletes_training_from_detail(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an existing training.
    admin = create_user(role="admin", email="admin@example.com")
    training = create_training(title="A borrar", category="gym", subtype="accumulation")
    log_in_as(admin)
    page.goto(f"{app_url}/entrenamientos/{training.id}")

    # When the admin deletes it and confirms.
    page.get_by_role("button", name="Eliminar").click()
    dialog = page.get_by_role("dialog", name="Eliminar entrenamiento")
    expect(dialog).to_be_visible()
    dialog.get_by_role("button", name="Eliminar").click()

    # Then a toast confirms it and they return to the trainings landing page.
    expect(page.get_by_role("status").filter(has_text="Entrenamiento eliminado.")).to_be_visible()
    expect(page).to_have_url(f"{app_url}/entrenamientos")

    # And it no longer appears in its subtype list.
    page.goto(f"{app_url}/entrenamientos/gimnasio/acumulacion")
    expect(page.get_by_role("button", name="A borrar")).not_to_be_visible()
    expect(page.get_by_text("Todavía no hay entrenamientos en este subtipo.")).to_be_visible()


def test_delete_can_be_cancelled(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given the detail page of a training.
    admin = create_user(role="admin", email="admin@example.com")
    training = create_training(title="No borrar", category="gym", subtype="accumulation")
    log_in_as(admin)
    page.goto(f"{app_url}/entrenamientos/{training.id}")

    # When the admin opens the delete dialog but cancels.
    page.get_by_role("button", name="Eliminar").click()
    page.get_by_role("button", name="Cancelar").click()

    # Then the training is still there.
    expect(page.get_by_role("dialog")).not_to_be_visible()
    expect(page.get_by_role("heading", name="No borrar")).to_be_visible()
