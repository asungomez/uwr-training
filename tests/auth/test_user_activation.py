from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import User


def test_deactivate_then_activate_user(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an admin viewing an active user's detail page.
    admin = create_user(role="admin", email="admin@example.com")
    target = create_user(role="member", email="target@example.com")
    log_in_as(admin)
    page.goto(f"{app_url}/usuarios/{target.id}")
    expect(page.get_by_text("Activo")).to_be_visible()

    # When I deactivate them.
    page.get_by_role("button", name="Desactivar").click()

    # Then the status flips to inactive and the button becomes "Activar".
    expect(page.get_by_text("Inactivo")).to_be_visible()
    expect(page.get_by_role("button", name="Activar")).to_be_visible()

    # When I activate them again.
    page.get_by_role("button", name="Activar").click()

    # Then they're active once more.
    expect(page.get_by_text("Activo")).to_be_visible()
    expect(page.get_by_role("button", name="Desactivar")).to_be_visible()


def test_no_activation_button_for_invitation(
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

    # When I open that invitation's detail page.
    page.get_by_role("cell", name="invitee@example.com").click()
    # The status field on the detail page shows it's a pending invitation.
    expect(page.get_by_role("definition").filter(has_text="Invitación pendiente")).to_be_visible()

    # Then there is no activate/deactivate action.
    expect(page.get_by_role("button", name="Desactivar")).not_to_be_visible()
    expect(page.get_by_role("button", name="Activar")).not_to_be_visible()
