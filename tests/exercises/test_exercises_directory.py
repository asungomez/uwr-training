from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import Exercise, User


def test_created_exercise_appears_as_card(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an exercise exists.
    admin = create_user(role="admin", email="admin@example.com")
    create_exercise(name="Sentadilla", type="gym")
    log_in_as(admin)

    # When the admin opens the exercises page.
    page.goto(f"{app_url}/ejercicios")

    # Then it shows up as a card.
    expect(page.get_by_role("heading", name="Sentadilla")).to_be_visible()


def test_filter_by_type(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a gym and a pool exercise.
    admin = create_user(role="admin", email="admin@example.com")
    create_exercise(name="Press banca", type="gym")
    create_exercise(name="Apnea", type="pool")
    log_in_as(admin)
    page.goto(f"{app_url}/ejercicios")

    # When I filter by Piscina.
    page.get_by_label("Filtrar por tipo").select_option(label="Piscina")

    # Then only the pool exercise remains.
    expect(page.get_by_role("heading", name="Apnea")).to_be_visible()
    expect(page.get_by_role("heading", name="Press banca")).not_to_be_visible()


def test_search_by_name(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # Given two exercises.
    admin = create_user(role="admin", email="admin@example.com")
    create_exercise(name="Dominadas", type="gym")
    create_exercise(name="Buceo", type="pool")
    log_in_as(admin)
    page.goto(f"{app_url}/ejercicios")

    # When I search by a partial name.
    page.get_by_label("Buscar").fill("domi")

    # Then only the match shows.
    expect(page.get_by_role("heading", name="Dominadas")).to_be_visible()
    expect(page.get_by_role("heading", name="Buceo")).not_to_be_visible()
