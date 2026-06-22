import re
from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import User


def test_regenerate_invitation_shows_new_link(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an admin who has created an invitation.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    page.goto(f"{app_url}/usuarios")
    page.get_by_role("button", name="Invitar nuevo usuario").click()
    page.get_by_label("Correo electrónico").fill("invitee@example.com")
    page.get_by_role("button", name="Enviar invitación").click()
    expect(page.get_by_label("Enlace de invitación")).to_be_visible()
    page.get_by_role("button", name="Cerrar").click()

    # When I open the invitation detail and regenerate it.
    page.get_by_role("cell", name="invitee@example.com").click()
    page.get_by_role("button", name="Generar nueva invitación").click()

    # Then a modal shows a fresh invitation link to copy.
    link = page.get_by_label("Enlace de invitación")
    expect(link).to_be_visible()
    expect(link).to_have_value(re.compile(r"/aceptar-invitacion/.+"))


def test_no_regenerate_button_for_user(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an admin viewing a real user's detail page.
    admin = create_user(role="admin", email="admin@example.com")
    target = create_user(role="member", email="member@example.com")
    log_in_as(admin)
    page.goto(f"{app_url}/usuarios/{target.id}")
    expect(page.get_by_text("Correo electrónico")).to_be_visible()

    # Then there is no regenerate action (users aren't invitations).
    expect(page.get_by_role("button", name="Generar nueva invitación")).not_to_be_visible()
