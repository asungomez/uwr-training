from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import User


def _generate_code(page: Page, app_url: str, user_id: str) -> str:
    """As an admin, open the user's detail page and generate a reset code."""
    page.goto(f"{app_url}/usuarios/{user_id}")
    page.get_by_role("button", name="Generar código de verificación").click()
    code = page.get_by_role("textbox", name="Código de verificación")
    expect(code).to_be_visible()
    return code.input_value()


def test_admin_generates_code_and_user_resets_password(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an admin generates a reset code for a member.
    admin = create_user(role="admin", email="admin@example.com")
    member = create_user(role="member", email="member@example.com")
    log_in_as(admin)
    code = _generate_code(page, app_url, str(member.id))

    # When the member (logged out) resets their password with email + code.
    page.context.clear_cookies()
    page.goto(f"{app_url}/recuperar-contrasena")
    page.get_by_label("Correo electrónico").fill("member@example.com")
    page.get_by_label("Código de verificación").fill(code)
    page.get_by_label("Nueva contraseña").fill("brandnewpass1")
    page.get_by_label("Repite la contraseña").fill("brandnewpass1")
    page.get_by_role("button", name="Cambiar contraseña").click()

    # Then they land on login and can sign in with the new password.
    expect(page.get_by_role("button", name="Iniciar sesión")).to_be_visible()
    page.get_by_label("Correo electrónico").fill("member@example.com")
    page.get_by_label("Contraseña", exact=True).fill("brandnewpass1")
    page.get_by_role("button", name="Iniciar sesión").click()
    expect(page.get_by_role("link", name="Entrenamientos")).to_be_visible()


def test_reset_code_cannot_be_used_twice(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an admin generated a code and the member used it once.
    admin = create_user(role="admin", email="admin@example.com")
    member = create_user(role="member", email="member@example.com")
    log_in_as(admin)
    code = _generate_code(page, app_url, str(member.id))

    page.context.clear_cookies()
    page.goto(f"{app_url}/recuperar-contrasena")
    page.get_by_label("Correo electrónico").fill("member@example.com")
    page.get_by_label("Código de verificación").fill(code)
    page.get_by_label("Nueva contraseña").fill("firstchange1")
    page.get_by_label("Repite la contraseña").fill("firstchange1")
    page.get_by_role("button", name="Cambiar contraseña").click()
    expect(page.get_by_role("button", name="Iniciar sesión")).to_be_visible()

    # When the member tries to reuse the same (now consumed) code.
    page.goto(f"{app_url}/recuperar-contrasena")
    page.get_by_label("Correo electrónico").fill("member@example.com")
    page.get_by_label("Código de verificación").fill(code)
    page.get_by_label("Nueva contraseña").fill("secondchange1")
    page.get_by_label("Repite la contraseña").fill("secondchange1")
    page.get_by_role("button", name="Cambiar contraseña").click()

    # Then it's rejected.
    expect(page.get_by_role("alert")).to_have_text(
        "El código de verificación no es válido o ha caducado."
    )


def test_forgot_password_wrong_code_shows_error(
    page: Page,
    app_url: str,
) -> None:
    # Given the public forgot-password page (no code arranged).
    page.goto(f"{app_url}/recuperar-contrasena")

    # When submitting an email + bogus code.
    page.get_by_label("Correo electrónico").fill("whoever@example.com")
    page.get_by_label("Código de verificación").fill("BOGUS123")
    page.get_by_label("Nueva contraseña").fill("brandnewpass1")
    page.get_by_label("Repite la contraseña").fill("brandnewpass1")
    page.get_by_role("button", name="Cambiar contraseña").click()

    # Then the localized invalid-code error shows.
    expect(page.get_by_role("alert")).to_have_text(
        "El código de verificación no es válido o ha caducado."
    )


def test_forgot_password_mismatch_blocks_submit(
    page: Page,
    app_url: str,
) -> None:
    page.goto(f"{app_url}/recuperar-contrasena")
    page.get_by_label("Correo electrónico").fill("whoever@example.com")
    page.get_by_label("Código de verificación").fill("ABCD1234")
    page.get_by_label("Nueva contraseña").fill("brandnewpass1")
    page.get_by_label("Repite la contraseña").fill("different2")
    page.get_by_role("button", name="Cambiar contraseña").click()

    expect(page.get_by_text("Las contraseñas no coinciden")).to_be_visible()


def test_login_has_forgot_password_link(page: Page, app_url: str) -> None:
    # Given the login screen, there's a link to recover the password.
    page.goto(app_url)
    page.get_by_role("link", name="Olvidé mi contraseña").click()
    expect(page).to_have_url(f"{app_url}/recuperar-contrasena")
    expect(
        page.get_by_text("Pide al administrador tu código de verificación", exact=False)
    ).to_be_visible()
