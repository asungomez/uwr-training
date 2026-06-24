from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import TrainingSession, User


def test_list_row_links_to_detail(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a training in the list.
    member = create_user(role="member", email="member@example.com")
    training = create_training(title="Fuerza máxima", category="gym", subtype="accumulation")
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos")

    # When I click its row.
    page.get_by_role("cell", name="Fuerza máxima").click()

    # Then I land on its detail page.
    expect(page).to_have_url(f"{app_url}/entrenamientos/{training.id}")
    expect(page.get_by_role("heading", name="Fuerza máxima")).to_be_visible()


def test_detail_shows_title_and_badges(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a training.
    member = create_user(role="member", email="member@example.com")
    training = create_training(title="Apnea larga", category="pool", subtype="endurance")
    log_in_as(member)

    # When I open its detail page.
    page.goto(f"{app_url}/entrenamientos/{training.id}")

    # Then the title heading and the category/subtype badges show.
    expect(page.get_by_role("heading", name="Apnea larga")).to_be_visible()
    expect(page.get_by_text("Piscina")).to_be_visible()
    expect(page.get_by_text("Resistencia")).to_be_visible()


def test_detail_breadcrumb_returns_to_list(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given the detail page of a training.
    member = create_user(role="member", email="member@example.com")
    training = create_training(title="Fuerza máxima", category="gym", subtype="accumulation")
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos/{training.id}")

    # When I click the breadcrumb back to the list.
    page.get_by_label("Migas de pan").get_by_role("link", name="Entrenamientos").click()

    # Then I'm on the list.
    expect(page).to_have_url(f"{app_url}/entrenamientos")
    expect(page.get_by_role("heading", name="Entrenamientos")).to_be_visible()


def test_detail_unknown_id_shows_not_found(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a logged-in user and a non-existent training id.
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)

    # When I open a detail URL that doesn't exist, a not-found message shows.
    page.goto(f"{app_url}/entrenamientos/00000000-0000-0000-0000-000000000000")
    expect(page.get_by_text("No se ha encontrado el entrenamiento.")).to_be_visible()
