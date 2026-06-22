from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import User


def test_search_filters_by_partial_email(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an admin and a few users with distinct emails.
    admin = create_user(role="admin", email="admin@example.com")
    create_user(role="member", email="alice@foo.com")
    create_user(role="member", email="bob@bar.com")
    log_in_as(admin)
    page.goto(f"{app_url}/usuarios")

    # When I search for a partial, differently-cased fragment.
    page.get_by_label("Buscar").fill("FOO")

    # Then only matching rows remain.
    expect(page.get_by_role("cell", name="alice@foo.com")).to_be_visible()
    expect(page.get_by_role("cell", name="bob@bar.com")).not_to_be_visible()


def test_clearing_search_restores_full_list(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a filtered list.
    admin = create_user(role="admin", email="admin@example.com")
    create_user(role="member", email="bob@bar.com")
    log_in_as(admin)
    page.goto(f"{app_url}/usuarios")
    page.get_by_label("Buscar").fill("foo")
    expect(page.get_by_role("cell", name="bob@bar.com")).not_to_be_visible()

    # When I clear the search.
    page.get_by_role("button", name="Limpiar búsqueda").click()

    # Then the full list is back.
    expect(page.get_by_role("cell", name="bob@bar.com")).to_be_visible()
    expect(page.get_by_role("cell", name="admin@example.com")).to_be_visible()


def test_search_with_no_matches_shows_message(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a logged-in admin.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    page.goto(f"{app_url}/usuarios")

    # When I search for something that matches nothing.
    page.get_by_label("Buscar").fill("zzzznomatch")

    # Then an empty-results message is shown.
    expect(page.get_by_text("No hay usuarios que coincidan con la búsqueda.")).to_be_visible()


def test_search_resets_to_first_page(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a two-page directory, viewing page two.
    admin = create_user(role="admin", email="admin@example.com")
    for i in range(12):
        create_user(role="member", email=f"user{i:02d}@example.com")
    log_in_as(admin)
    page.goto(f"{app_url}/usuarios")
    pager = page.locator("[aria-label='Paginación']")
    pager.get_by_role("button", name="2").click()
    expect(pager.get_by_role("button", name="2")).to_have_attribute("aria-current", "page")

    # When I run a search that still spans multiple results.
    page.get_by_label("Buscar").fill("user")

    # Then I'm back on page one.
    expect(pager.get_by_role("button", name="1")).to_have_attribute("aria-current", "page")
