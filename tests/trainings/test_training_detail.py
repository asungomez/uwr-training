from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import TrainingBlock, TrainingSession, User


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


def test_detail_shows_blocks_in_order(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a training with three ordered blocks.
    member = create_user(role="member", email="member@example.com")
    training = create_training(
        title="Sesión completa",
        category="gym",
        subtype="accumulation",
        blocks=[
            TrainingBlock(name="Calentamiento", position=0),
            TrainingBlock(name="Tren superior", position=1),
            TrainingBlock(name="Vuelta a la calma", position=2),
        ],
    )
    log_in_as(member)

    # When I open its detail page.
    page.goto(f"{app_url}/entrenamientos/{training.id}")

    # Then each block shows its name as a heading, with the placeholder text.
    headings = page.get_by_role("heading", level=2)
    expect(headings).to_have_count(3)
    expect(headings.nth(0)).to_have_text("Calentamiento")
    expect(headings.nth(1)).to_have_text("Tren superior")
    expect(headings.nth(2)).to_have_text("Vuelta a la calma")
    expect(page.get_by_text("Aquí irá el bloque de entrenamiento.")).to_have_count(3)


def test_detail_without_blocks_shows_no_block_section(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a training with no blocks.
    member = create_user(role="member", email="member@example.com")
    training = create_training(title="Vacía", category="gym", subtype="accumulation")
    log_in_as(member)

    # When I open its detail page, no block placeholder appears.
    page.goto(f"{app_url}/entrenamientos/{training.id}")
    expect(page.get_by_role("heading", name="Vacía")).to_be_visible()
    expect(page.get_by_text("Aquí irá el bloque de entrenamiento.")).to_have_count(0)
