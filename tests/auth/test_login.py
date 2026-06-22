from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import User
from seeding.user.factory import DEFAULT_PASSWORD


def test_login_fails_for_unregistered_user(
    page: Page,
    app_url: str,
    generate_user: Callable[..., User],
) -> None:
    # Given a user that does not exist in the system (built, never persisted).
    user = generate_user()

    # When I try to log in as that user.
    page.goto(app_url)
    page.get_by_label("Correo electrónico").fill(user.email)
    page.get_by_label("Contraseña").fill(DEFAULT_PASSWORD)
    page.get_by_role("button", name="Iniciar sesión").click()

    # Then login fails: an error is shown and I stay on the login form.
    expect(page.get_by_role("alert")).to_have_text(
        "Correo electrónico o contraseña incorrectos"
    )
    expect(page.get_by_role("button", name="Iniciar sesión")).to_be_visible()


def test_login_fails_with_wrong_password(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
) -> None:
    # Given a registered user.
    user = create_user()

    # When I log in with the right email but a wrong password.
    page.goto(app_url)
    page.get_by_label("Correo electrónico").fill(user.email)
    page.get_by_label("Contraseña").fill("definitely-not-the-password")
    page.get_by_role("button", name="Iniciar sesión").click()

    # Then login fails: an error is shown and I stay on the login form.
    expect(page.get_by_role("alert")).to_have_text(
        "Correo electrónico o contraseña incorrectos"
    )
    expect(page.get_by_role("button", name="Iniciar sesión")).to_be_visible()


def test_login_succeeds_with_valid_credentials(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
) -> None:
    # Given a registered user.
    user = create_user()

    # When I log in with the correct credentials.
    page.goto(app_url)
    page.get_by_label("Correo electrónico").fill(user.email)
    page.get_by_label("Contraseña").fill(DEFAULT_PASSWORD)
    page.get_by_role("button", name="Iniciar sesión").click()

    # Then I land on the app shell (the menu's Entrenamientos section is shown).
    expect(page.get_by_role("link", name="Entrenamientos")).to_be_visible()
    expect(page.get_by_role("button", name="Iniciar sesión")).not_to_be_visible()


def test_login_shows_validation_errors_on_empty_submit(
    page: Page,
    app_url: str,
) -> None:
    # Given the login form (no input filled).
    page.goto(app_url)

    # When I submit without entering anything.
    page.get_by_role("button", name="Iniciar sesión").click()

    # Then client-side validation blocks it and shows field messages.
    expect(page.get_by_text("Introduce un correo electrónico válido")).to_be_visible()
    expect(page.get_by_text("La contraseña es obligatoria")).to_be_visible()
