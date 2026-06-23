import re
from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import Exercise, User


def test_search_and_filter_reflected_in_url(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a gym and a pool exercise.
    admin = create_user(role="admin", email="admin@example.com")
    create_exercise(name="Apnea", type="pool")
    create_exercise(name="Sentadilla", type="gym")
    log_in_as(admin)
    page.goto(f"{app_url}/ejercicios")

    # When I filter, then search.
    page.get_by_label("Filtrar por tipo").select_option(label="Piscina")
    expect(page).to_have_url(re.compile(r"[?&]type=pool"))
    page.get_by_label("Buscar").fill("apn")

    # Then the URL captures both, so it's shareable.
    expect(page).to_have_url(re.compile(r"[?&]q=apn"))
    expect(page).to_have_url(re.compile(r"[?&]type=pool"))


def test_deep_link_restores_search_and_filter(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # Given two exercises of different types.
    admin = create_user(role="admin", email="admin@example.com")
    create_exercise(name="Dominadas", type="gym")
    create_exercise(name="Buceo", type="pool")
    log_in_as(admin)

    # When I open a URL that already carries search + filter.
    page.goto(f"{app_url}/ejercicios?q=domi&type=gym")

    # Then the controls are pre-filled and the list is already filtered.
    expect(page.get_by_label("Buscar")).to_have_value("domi")
    expect(page.get_by_label("Filtrar por tipo")).to_have_value("gym")
    expect(page.get_by_role("heading", name="Dominadas")).to_be_visible()
    expect(page.get_by_role("heading", name="Buceo")).not_to_be_visible()


def test_bogus_filter_in_url_is_ignored(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an exercise and a hand-edited URL with an invalid type.
    admin = create_user(role="admin", email="admin@example.com")
    create_exercise(name="Zancadas", type="gym")
    log_in_as(admin)
    page.goto(f"{app_url}/ejercicios?type=garbage")

    # Then the filter falls back to "all" and the list still loads.
    expect(page.get_by_label("Filtrar por tipo")).to_have_value("")
    expect(page.get_by_role("heading", name="Zancadas")).to_be_visible()
