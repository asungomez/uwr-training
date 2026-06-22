import re
from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import User


def test_clicking_row_opens_detail(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a logged-in admin and another user.
    admin = create_user(role="admin", email="admin@example.com")
    create_user(role="member", email="member@example.com")
    log_in_as(admin)
    page.goto(f"{app_url}/usuarios")

    # When I click the member's row.
    page.get_by_role("cell", name="member@example.com").click()

    # Then I land on the detail page showing their fields.
    expect(page).to_have_url(re.compile(r"/usuarios/[0-9a-f-]+$"))
    expect(page.get_by_text("Correo electrónico")).to_be_visible()
    expect(page.get_by_text("Invitación expira en")).to_be_visible()


def test_breadcrumb_returns_to_list(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an admin viewing a user detail page.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    page.goto(f"{app_url}/usuarios")
    page.get_by_role("cell", name="admin@example.com").click()
    expect(page.get_by_text("Correo electrónico")).to_be_visible()

    # When I click the Usuarios breadcrumb.
    page.get_by_role("link", name="Usuarios").click()

    # Then I'm back on the list.
    expect(page).to_have_url(f"{app_url}/usuarios")
    expect(page.get_by_role("button", name="Invitar nuevo usuario")).to_be_visible()


def test_member_cannot_access_user_detail(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a logged-in member and some other user's id.
    other = create_user(role="member", email="other@example.com")
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)

    # When I try to open a user detail page directly.
    page.goto(f"{app_url}/usuarios/{other.id}")

    # Then I'm redirected away.
    expect(page).to_have_url(f"{app_url}/entrenamientos")
