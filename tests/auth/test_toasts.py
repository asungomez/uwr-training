from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import User


def _invite_and_get_link(page: Page, app_url: str, email: str) -> str:
    page.goto(f"{app_url}/usuarios")
    page.get_by_role("button", name="Invitar nuevo usuario").click()
    page.get_by_label("Correo electrónico").fill(email)
    page.get_by_role("button", name="Enviar invitación").click()
    link = page.get_by_label("Enlace de invitación")
    expect(link).to_be_visible()
    return link.input_value()


def test_accept_shows_success_toast(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an invitation link.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    link = _invite_and_get_link(page, app_url, "newbie@example.com")

    # When the invitee accepts it.
    page.context.clear_cookies()
    page.goto(link)
    page.get_by_label("Correo electrónico").fill("newbie@example.com")
    page.get_by_label("Contraseña", exact=True).fill("newpassword1")
    page.get_by_label("Repite la contraseña").fill("newpassword1")
    page.get_by_role("button", name="Crear cuenta").click()

    # Then a success toast confirms the account was created.
    expect(page.get_by_role("status").filter(has_text="Cuenta creada")).to_be_visible()


def test_deactivate_shows_toast(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an admin on an active user's detail page.
    admin = create_user(role="admin", email="admin@example.com")
    target = create_user(role="member", email="target@example.com")
    log_in_as(admin)
    page.goto(f"{app_url}/usuarios/{target.id}")

    # When they deactivate the user.
    page.get_by_role("button", name="Desactivar").click()

    # Then a toast confirms it.
    expect(page.get_by_role("status").filter(has_text="Usuario desactivado.")).to_be_visible()
