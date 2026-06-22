from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import User


def _filter_by_role(page: Page, label: str) -> None:
    page.get_by_label("Filtrar por rol").select_option(label=label)


def _filter_by_status(page: Page, label: str) -> None:
    page.get_by_label("Filtrar por estado").select_option(label=label)


def test_filter_by_role(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an admin and a member.
    admin = create_user(role="admin", email="admin@example.com")
    create_user(role="member", email="member@example.com")
    log_in_as(admin)
    page.goto(f"{app_url}/usuarios")

    # When I filter by the member role.
    _filter_by_role(page, "Miembro")

    # Then only members remain.
    expect(page.get_by_role("cell", name="member@example.com")).to_be_visible()
    expect(page.get_by_role("cell", name="admin@example.com")).not_to_be_visible()


def test_status_active_shows_only_users(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an active user and a pending invitation.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    page.goto(f"{app_url}/usuarios")
    page.get_by_role("button", name="Invitar nuevo usuario").click()
    page.get_by_label("Correo electrónico").fill("pending@example.com")
    page.get_by_role("button", name="Enviar invitación").click()
    expect(page.get_by_label("Enlace de invitación")).to_be_visible()
    page.get_by_role("button", name="Cerrar").click()

    # When I filter by the "active" status.
    _filter_by_status(page, "Activo")

    # Then only the (active) user shows; the pending invitation is scoped out.
    expect(page.get_by_role("cell", name="admin@example.com")).to_be_visible()
    expect(page.get_by_role("cell", name="pending@example.com")).not_to_be_visible()


def test_status_pending_shows_only_invitations(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an active user and a pending invitation.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    page.goto(f"{app_url}/usuarios")
    page.get_by_role("button", name="Invitar nuevo usuario").click()
    page.get_by_label("Correo electrónico").fill("pending@example.com")
    page.get_by_role("button", name="Enviar invitación").click()
    expect(page.get_by_label("Enlace de invitación")).to_be_visible()
    page.get_by_role("button", name="Cerrar").click()

    # When I filter by the "pending invitation" status.
    _filter_by_status(page, "Invitación pendiente")

    # Then only the invitation shows; the user is scoped out.
    expect(page.get_by_role("cell", name="pending@example.com")).to_be_visible()
    expect(page.get_by_role("cell", name="admin@example.com")).not_to_be_visible()
