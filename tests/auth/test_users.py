from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import User


def test_admin_sees_user_list(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a logged-in admin and a couple of other users.
    admin = create_user(role="admin", email="admin@example.com")
    create_user(role="member", email="member@example.com")
    log_in_as(admin)

    # When I open the users page.
    page.goto(f"{app_url}/usuarios")

    # Then every user is listed with their email (desktop table cells).
    expect(page.get_by_role("cell", name="admin@example.com")).to_be_visible()
    expect(page.get_by_role("cell", name="member@example.com")).to_be_visible()


def test_member_cannot_access_users(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a logged-in member.
    member = create_user(role="member")
    log_in_as(member)

    # When I try to navigate directly to the admin users page.
    page.goto(f"{app_url}/usuarios")

    # Then I'm redirected away (to Entrenamientos) and don't see the user list.
    expect(page).to_have_url(f"{app_url}/entrenamientos")
