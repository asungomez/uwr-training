from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import User


def test_member_sidebar_hides_admin_section(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a logged-in member.
    member = create_user(role="member")
    log_in_as(member)

    # When I open the app.
    page.goto(app_url)

    # Then the regular menu shows, but the admin section does not.
    expect(page.get_by_role("link", name="Entrenamientos")).to_be_visible()
    expect(page.get_by_text("Administración")).not_to_be_visible()
    expect(page.get_by_role("link", name="Usuarios")).not_to_be_visible()


def test_admin_sidebar_shows_admin_section(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a logged-in admin.
    admin = create_user(role="admin")
    log_in_as(admin)

    # When I open the app.
    page.goto(app_url)

    # Then both the regular menu and the admin section show.
    expect(page.get_by_role("link", name="Entrenamientos")).to_be_visible()
    expect(page.get_by_text("Administración")).to_be_visible()
    expect(page.get_by_role("link", name="Usuarios")).to_be_visible()
