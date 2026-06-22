from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import User

PAGER = "[aria-label='Paginación']"


def _seed_members(create_user: Callable[..., User], count: int) -> None:
    # Zero-padded emails keep the email sort order predictable across pages.
    for i in range(count):
        create_user(role="member", email=f"user{i:02d}@example.com")


def test_no_pager_with_a_single_page(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given fewer users than one page holds (admin + 3 = 4, page size is 10).
    admin = create_user(role="admin", email="admin@example.com")
    _seed_members(create_user, 3)
    log_in_as(admin)

    # When I open the users page.
    page.goto(f"{app_url}/usuarios")

    # Then the list renders but there is no pagination control.
    expect(page.get_by_role("cell", name="user00@example.com")).to_be_visible()
    expect(page.locator(PAGER)).not_to_be_visible()


def test_pager_appears_with_multiple_pages(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given more users than one page holds (admin + 12 = 13 → 2 pages).
    admin = create_user(role="admin", email="admin@example.com")
    _seed_members(create_user, 12)
    log_in_as(admin)

    # When I open the users page.
    page.goto(f"{app_url}/usuarios")

    # Then a pager shows with a second page, and page one holds exactly 10 rows.
    expect(page.locator(PAGER)).to_be_visible()
    expect(page.locator(PAGER).get_by_role("button", name="2")).to_be_visible()
    expect(page.locator("tbody tr")).to_have_count(10)


def test_changing_page_shows_next_results(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a two-page directory (admin@ + user00..user11, sorted by email).
    admin = create_user(role="admin", email="admin@example.com")
    _seed_members(create_user, 12)
    log_in_as(admin)
    page.goto(f"{app_url}/usuarios")

    # The last entries are not on page one...
    expect(page.get_by_role("cell", name="user11@example.com")).not_to_be_visible()

    # When I go to page two.
    page.locator(PAGER).get_by_role("button", name="2").click()

    # Then the later entries show and the first page's first entry is gone.
    expect(page.get_by_role("cell", name="user11@example.com")).to_be_visible()
    expect(page.get_by_role("cell", name="admin@example.com")).not_to_be_visible()
