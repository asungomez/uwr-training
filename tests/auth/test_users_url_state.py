import re
from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import User


def test_search_and_filter_reflected_in_url(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an admin and members.
    admin = create_user(role="admin", email="admin@example.com")
    create_user(role="member", email="alice@foo.com")
    log_in_as(admin)
    page.goto(f"{app_url}/usuarios")

    # When I filter by role and search.
    page.get_by_label("Filtrar por rol").select_option(label="Miembro")
    expect(page).to_have_url(re.compile(r"[?&]role=member"))
    page.get_by_label("Buscar").fill("ali")

    # Then the URL captures both.
    expect(page).to_have_url(re.compile(r"[?&]q=ali"))
    expect(page).to_have_url(re.compile(r"[?&]role=member"))


def test_deep_link_restores_search_and_filter(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an admin and a couple of members.
    admin = create_user(role="admin", email="admin@example.com")
    create_user(role="member", email="alice@foo.com")
    create_user(role="member", email="bob@bar.com")
    log_in_as(admin)

    # When I open a URL carrying search + role filter.
    page.goto(f"{app_url}/usuarios?q=ali&role=member")

    # Then the controls are pre-filled and the list is filtered.
    expect(page.get_by_label("Buscar")).to_have_value("ali")
    expect(page.get_by_label("Filtrar por rol")).to_have_value("member")
    expect(page.get_by_role("cell", name="alice@foo.com")).to_be_visible()
    expect(page.get_by_role("cell", name="bob@bar.com")).not_to_be_visible()


def test_deep_link_restores_page(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a two-page directory.
    admin = create_user(role="admin", email="admin@example.com")
    for i in range(12):
        create_user(role="member", email=f"user{i:02d}@example.com")
    log_in_as(admin)

    # When I open page two directly via the URL.
    page.goto(f"{app_url}/usuarios?page=2")

    # Then the pager shows page two as current.
    pager = page.locator("[aria-label='Paginación']")
    expect(pager.get_by_role("button", name="2")).to_have_attribute("aria-current", "page")


def test_paging_updates_url(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a two-page directory on page one.
    admin = create_user(role="admin", email="admin@example.com")
    for i in range(12):
        create_user(role="member", email=f"user{i:02d}@example.com")
    log_in_as(admin)
    page.goto(f"{app_url}/usuarios")

    # When I go to page two.
    pager = page.locator("[aria-label='Paginación']")
    pager.get_by_role("button", name="2").click()

    # Then the URL reflects it.
    expect(page).to_have_url(re.compile(r"[?&]page=2"))
