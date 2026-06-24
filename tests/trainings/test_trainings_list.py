import re
from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import TrainingSession, User


# ---------------------------------------------------------------- landing page


def test_landing_shows_category_cards(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a logged-in user on the trainings landing page.
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos")

    # Then the three category cards are shown as links to their pages. Scope to
    # main — the sidebar also has these category links.
    main = page.get_by_role("main")
    expect(main.get_by_role("link", name="Gimnasio")).to_have_attribute(
        "href", "/entrenamientos/gimnasio"
    )
    expect(main.get_by_role("link", name="Piscina")).to_have_attribute(
        "href", "/entrenamientos/piscina"
    )
    expect(main.get_by_role("link", name="Cardio")).to_have_attribute(
        "href", "/entrenamientos/cardio"
    )


def test_landing_card_navigates_to_category(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given the landing page.
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos")

    # When I click the Piscina card (scope to main — the sidebar has the link too).
    page.get_by_role("main").get_by_role("link", name="Piscina").click()

    # Then I land on that category's list, headed by its name.
    expect(page).to_have_url(f"{app_url}/entrenamientos/piscina")
    expect(page.get_by_role("main").get_by_role("heading", name="Piscina")).to_be_visible()


# ------------------------------------------------------------ category list page


def test_category_list_shows_only_its_trainings(
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

    # When I open the gym category page.
    page.goto(f"{app_url}/entrenamientos/gimnasio")

    # Then only the gym training shows, with its subtype; the pool one does not.
    expect(page.get_by_role("cell", name="Fuerza máxima")).to_be_visible()
    expect(page.get_by_role("cell", name="Acumulación")).to_be_visible()
    expect(page.get_by_role("cell", name="Apnea larga")).not_to_be_visible()


def test_empty_category_shows_message(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given no trainings.
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)

    # When I open a category page, an empty message shows.
    page.goto(f"{app_url}/entrenamientos/cardio")
    expect(page.get_by_text("Todavía no hay entrenamientos en esta categoría.")).to_be_visible()


def test_search_filters_by_title_within_category(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given two gym trainings.
    member = create_user(role="member", email="member@example.com")
    create_training(title="Fuerza máxima", category="gym", subtype="accumulation")
    create_training(title="Dominadas", category="gym", subtype="realization")
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos/gimnasio")

    # When I search by a partial title.
    page.get_by_label("Buscar").fill("fuerza")

    # Then only the match remains.
    expect(page.get_by_role("cell", name="Fuerza máxima")).to_be_visible()
    expect(page.get_by_role("cell", name="Dominadas")).not_to_be_visible()


def test_subtype_filter_offers_only_category_subtypes(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given the gym category page.
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos/gimnasio")

    # Then the subtype filter offers gym subtypes, not pool ones.
    subtype = page.get_by_label("Filtrar por subtipo")
    expect(subtype.get_by_role("option", name="Acumulación")).to_be_attached()
    expect(subtype.get_by_role("option", name="Realización")).to_be_attached()
    expect(subtype.get_by_role("option", name="Resistencia")).to_have_count(0)


def test_filter_by_subtype_within_category(
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
    page.goto(f"{app_url}/entrenamientos/gimnasio")

    # When I filter by the Realización subtype.
    page.get_by_label("Filtrar por subtipo").select_option(label="Realización")

    # Then only that training remains.
    expect(page.get_by_role("cell", name="Bloque realización")).to_be_visible()
    expect(page.get_by_role("cell", name="Bloque acumulación")).not_to_be_visible()


def test_subtype_filter_reflected_in_url(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given the gym category page.
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos/gimnasio")

    # When I set a subtype filter, it's captured in the URL (shareable).
    page.get_by_label("Filtrar por subtipo").select_option(label="Acumulación")
    expect(page).to_have_url(re.compile(r"[?&]subtype=accumulation"))


def test_member_does_not_see_create_button(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a logged-in member on a category page.
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)

    # Then there's no create button.
    page.goto(f"{app_url}/entrenamientos/gimnasio")
    expect(page.get_by_role("link", name="Nuevo entrenamiento")).not_to_be_visible()
