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

    # Then I land on that category's page, headed by its name.
    expect(page).to_have_url(f"{app_url}/entrenamientos/piscina")
    expect(page.get_by_role("main").get_by_role("heading", name="Piscina")).to_be_visible()


# ----------------------------------------------------- category page (subtype cards)


def test_category_shows_only_its_subtype_cards(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given the gym category page.
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos/gimnasio")

    # Then it shows the gym subtype cards (not pool ones), linking one level deeper.
    main = page.get_by_role("main")
    expect(main.get_by_role("link", name="Acumulación")).to_have_attribute(
        "href", "/entrenamientos/gimnasio/acumulacion"
    )
    expect(main.get_by_role("link", name="Realización")).to_have_attribute(
        "href", "/entrenamientos/gimnasio/realizacion"
    )
    expect(main.get_by_role("link", name="Resistencia")).to_have_count(0)


def test_category_card_navigates_to_subtype(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given the gym category page.
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos/gimnasio")

    # When I click a subtype card.
    page.get_by_role("main").get_by_role("link", name="Acumulación").click()

    # Then I land on that subtype's list, headed by its name.
    expect(page).to_have_url(f"{app_url}/entrenamientos/gimnasio/acumulacion")
    expect(page.get_by_role("main").get_by_role("heading", name="Acumulación")).to_be_visible()


def test_unknown_category_redirects_to_landing(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a logged-in user navigating from a category to a bogus subtype slug.
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)

    # An unknown subtype under a valid category sends me back to the category page.
    page.goto(f"{app_url}/entrenamientos/gimnasio/maraton")
    expect(page).to_have_url(f"{app_url}/entrenamientos/gimnasio")


# ------------------------------------------------------------ subtype list page


def test_subtype_list_shows_only_its_trainings(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given two gym trainings of different subtypes.
    member = create_user(role="member", email="member@example.com")
    create_training(title="Bloque acumulación", category="gym", subtype="accumulation")
    create_training(title="Bloque realización", category="gym", subtype="realization")
    log_in_as(member)

    # When I open the accumulation subtype list.
    page.goto(f"{app_url}/entrenamientos/gimnasio/acumulacion")

    # Then only the accumulation training shows.
    expect(page.get_by_role("button", name="Bloque acumulación")).to_be_visible()
    expect(page.get_by_role("button", name="Bloque realización")).not_to_be_visible()


def test_empty_subtype_shows_message(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given no trainings.
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)

    # When I open a subtype list, an empty message shows.
    page.goto(f"{app_url}/entrenamientos/gimnasio/acumulacion")
    expect(page.get_by_text("Todavía no hay entrenamientos en este subtipo.")).to_be_visible()


def test_search_filters_by_title_within_subtype(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given two accumulation trainings.
    member = create_user(role="member", email="member@example.com")
    create_training(title="Fuerza máxima", category="gym", subtype="accumulation")
    create_training(title="Dominadas", category="gym", subtype="accumulation")
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos/gimnasio/acumulacion")

    # When I search by a partial title.
    page.get_by_label("Buscar").fill("fuerza")

    # Then only the match remains.
    expect(page.get_by_role("button", name="Fuerza máxima")).to_be_visible()
    expect(page.get_by_role("button", name="Dominadas")).not_to_be_visible()


def test_search_reflected_in_url(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a subtype list.
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos/gimnasio/acumulacion")

    # When I search, the term is captured in the URL (shareable).
    page.get_by_label("Buscar").fill("fuerza")
    expect(page).to_have_url(re.compile(r"[?&]q=fuerza"))


def test_subtype_excludes_other_category_with_shared_subtype(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # `anaerobic` belongs to both pool and cardio — the pool list must not leak the
    # cardio one (the list is scoped by BOTH category and subtype).
    member = create_user(role="member", email="member@example.com")
    create_training(title="Pool anaeróbico", category="pool", subtype="anaerobic")
    create_training(title="Cardio anaeróbico", category="cardio", subtype="anaerobic")
    log_in_as(member)

    page.goto(f"{app_url}/entrenamientos/piscina/anaerobico")
    expect(page.get_by_role("button", name="Pool anaeróbico")).to_be_visible()
    expect(page.get_by_role("button", name="Cardio anaeróbico")).not_to_be_visible()


def test_member_does_not_see_create_button(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a logged-in member on a subtype list.
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)

    # Then there's no create button.
    page.goto(f"{app_url}/entrenamientos/gimnasio/acumulacion")
    expect(page.get_by_role("link", name="Nuevo entrenamiento")).not_to_be_visible()


def test_select_multiple_trainings_exports_combined_pdf(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given two trainings in the same subtype list.
    member = create_user(role="member", email="member@example.com")
    create_training(title="Primera", category="gym", subtype="accumulation")
    create_training(title="Segunda", category="gym", subtype="accumulation")
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos/gimnasio/acumulacion")

    # The PDF action only appears once at least one row is selected.
    expect(page.get_by_role("button", name=re.compile(r"PDF"))).to_have_count(0)
    checkboxes = page.get_by_role("checkbox")
    checkboxes.nth(0).check()
    checkboxes.nth(1).check()

    # When I generate, a new tab opens with the combined client-generated PDF.
    pdf_button = page.get_by_role("button", name=re.compile(r"PDF \(2\)"))
    expect(pdf_button).to_be_visible()
    with page.context.expect_page() as new_page_info:
        pdf_button.click()
    pdf_page = new_page_info.value
    pdf_page.wait_for_load_state()
    src = pdf_page.evaluate(
        "() => { const el = document.querySelector('iframe,embed'); return el ? el.src : '' }"
    )
    assert src.startswith("data:application/pdf"), src


def test_select_all_and_deselect_all(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given three trainings in the same subtype list.
    member = create_user(role="member", email="member@example.com")
    for title in ("Una", "Dos", "Tres"):
        create_training(title=title, category="gym", subtype="accumulation")
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos/gimnasio/acumulacion")

    # "Seleccionar todo" ticks every row → "PDF (3)" and the toggle flips.
    page.get_by_role("button", name="Seleccionar todo").click()
    checkboxes = page.get_by_role("checkbox")
    expect(checkboxes.nth(0)).to_be_checked()
    expect(checkboxes.nth(1)).to_be_checked()
    expect(checkboxes.nth(2)).to_be_checked()
    expect(page.get_by_role("button", name=re.compile(r"PDF \(3\)"))).to_be_visible()

    # "Deseleccionar todo" clears them → the PDF button disappears.
    page.get_by_role("button", name="Deseleccionar todo").click()
    expect(checkboxes.nth(0)).not_to_be_checked()
    expect(page.get_by_role("button", name=re.compile(r"PDF \("))).to_have_count(0)
