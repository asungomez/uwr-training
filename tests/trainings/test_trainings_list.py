import re
from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import TrainingSession, User


def test_list_shows_trainings_with_category_and_subtype(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a couple of trainings.
    member = create_user(role="member", email="member@example.com")
    create_training(title="Fuerza máxima", category="gym", subtype="accumulation")
    create_training(title="Apnea larga", category="pool", subtype="endurance")
    log_in_as(member)

    # When the list loads.
    page.goto(f"{app_url}/entrenamientos")

    # Then each training shows its title, category and subtype.
    expect(page.get_by_role("cell", name="Fuerza máxima")).to_be_visible()
    expect(page.get_by_role("cell", name="Gimnasio")).to_be_visible()
    expect(page.get_by_role("cell", name="Acumulación")).to_be_visible()
    expect(page.get_by_role("cell", name="Apnea larga")).to_be_visible()
    expect(page.get_by_role("cell", name="Piscina")).to_be_visible()


def test_empty_list_shows_message(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given no trainings.
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)

    # When the list loads, an empty message shows.
    page.goto(f"{app_url}/entrenamientos")
    expect(page.get_by_text("Todavía no hay entrenamientos.")).to_be_visible()


def test_search_filters_by_title(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given two distinctly titled trainings.
    member = create_user(role="member", email="member@example.com")
    create_training(title="Fuerza máxima", category="gym", subtype="accumulation")
    create_training(title="Apnea larga", category="pool", subtype="endurance")
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos")

    # When I search by a partial title.
    page.get_by_label("Buscar").fill("fuerza")

    # Then only the match remains.
    expect(page.get_by_role("cell", name="Fuerza máxima")).to_be_visible()
    expect(page.get_by_role("cell", name="Apnea larga")).not_to_be_visible()


def test_filter_by_category(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a gym and a pool training.
    member = create_user(role="member", email="member@example.com")
    create_training(title="Fuerza máxima", category="gym", subtype="accumulation")
    create_training(title="Apnea larga", category="pool", subtype="endurance")
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos")

    # When I filter by Piscina.
    page.get_by_label("Filtrar por categoría").select_option(label="Piscina")

    # Then only the pool training remains.
    expect(page.get_by_role("cell", name="Apnea larga")).to_be_visible()
    expect(page.get_by_role("cell", name="Fuerza máxima")).not_to_be_visible()


def test_filter_by_subtype(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given two gym trainings with different subtypes.
    member = create_user(role="member", email="member@example.com")
    create_training(title="Bloque acumulación", category="gym", subtype="accumulation")
    create_training(title="Bloque realización", category="gym", subtype="realization")
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos")

    # When I filter by the Realización subtype.
    page.get_by_label("Filtrar por subtipo").select_option(label="Realización")

    # Then only that training remains.
    expect(page.get_by_role("cell", name="Bloque realización")).to_be_visible()
    expect(page.get_by_role("cell", name="Bloque acumulación")).not_to_be_visible()


def test_filters_are_reflected_in_url(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given the list page.
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos")

    # When I set a category filter, it's captured in the URL (shareable).
    page.get_by_label("Filtrar por categoría").select_option(label="Gimnasio")
    expect(page).to_have_url(re.compile(r"[?&]category=gym"))


def test_member_does_not_see_create_button(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a logged-in member.
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)

    # Then the trainings list has no create button.
    page.goto(f"{app_url}/entrenamientos")
    expect(page.get_by_role("link", name="Nuevo entrenamiento")).not_to_be_visible()
