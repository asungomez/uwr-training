from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import User


def _invite_and_get_link(page: Page, app_url: str, email: str) -> str:
    """Drive the admin invite modal and return the invitation link it shows."""
    page.goto(f"{app_url}/usuarios")
    page.get_by_role("button", name="Invitar nuevo usuario").click()
    page.get_by_label("Correo electrónico").fill(email)
    page.get_by_role("button", name="Enviar invitación").click()
    link = page.get_by_label("Enlace de invitación")
    expect(link).to_be_visible()
    return link.input_value()


def test_accept_invitation_creates_account_and_can_log_in(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an admin has invited someone (we grab the real link).
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    link = _invite_and_get_link(page, app_url, "newbie@example.com")

    # And the invitee opens the accept page (logged out).
    page.context.clear_cookies()
    page.goto(link)

    # When they fill matching email + password.
    page.get_by_label("Correo electrónico").fill("newbie@example.com")
    page.get_by_label("Contraseña", exact=True).fill("newpassword1")
    page.get_by_label("Repite la contraseña").fill("newpassword1")
    page.get_by_role("button", name="Crear cuenta").click()

    # Then they land on the login screen and can log in with the new credentials.
    expect(page.get_by_role("button", name="Iniciar sesión")).to_be_visible()
    page.get_by_label("Correo electrónico").fill("newbie@example.com")
    page.get_by_label("Contraseña", exact=True).fill("newpassword1")
    page.get_by_role("button", name="Iniciar sesión").click()
    expect(page.get_by_role("link", name="Entrenamientos")).to_be_visible()


def test_accept_invitation_wrong_email_shows_error(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an invitation for one email.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    link = _invite_and_get_link(page, app_url, "real@example.com")

    # When the invitee submits a different email.
    page.context.clear_cookies()
    page.goto(link)
    page.get_by_label("Correo electrónico").fill("wrong@example.com")
    page.get_by_label("Contraseña", exact=True).fill("newpassword1")
    page.get_by_label("Repite la contraseña").fill("newpassword1")
    page.get_by_role("button", name="Crear cuenta").click()

    # Then a Spanish mismatch error is shown.
    expect(page.get_by_role("alert")).to_have_text(
        "El correo electrónico no coincide con la invitación."
    )


def test_accept_invitation_password_mismatch_blocks_submit(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an invitation link.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    link = _invite_and_get_link(page, app_url, "typo@example.com")

    # When the two passwords don't match.
    page.context.clear_cookies()
    page.goto(link)
    page.get_by_label("Correo electrónico").fill("typo@example.com")
    page.get_by_label("Contraseña", exact=True).fill("newpassword1")
    page.get_by_label("Repite la contraseña").fill("different2")
    page.get_by_role("button", name="Crear cuenta").click()

    # Then client-side validation flags it.
    expect(page.get_by_text("Las contraseñas no coinciden")).to_be_visible()
