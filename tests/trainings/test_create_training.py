import re
from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import User


def test_admin_navigates_from_button_to_new_training(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a logged-in admin on a subtype list page.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    page.goto(f"{app_url}/entrenamientos/gimnasio/acumulacion")

    # When they click "Nuevo entrenamiento".
    page.get_by_role("link", name="Nuevo entrenamiento").click()

    # Then they land on the creation page.
    expect(page).to_have_url(f"{app_url}/entrenamientos/nuevo")
    expect(page.get_by_role("heading", name="Nuevo entrenamiento")).to_be_visible()


def test_member_does_not_see_new_training_button(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a logged-in member on a subtype list page (where an admin would see it).
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos/gimnasio/acumulacion")

    # Then there's no create button.
    expect(page.get_by_role("link", name="Nuevo entrenamiento")).not_to_be_visible()


def test_member_cannot_access_new_training_page(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a logged-in member.
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)

    # When they go straight to the creation URL, the admin guard redirects them
    # away to the trainings list (no creation form shown).
    page.goto(f"{app_url}/entrenamientos/nuevo")
    expect(page.get_by_role("button", name="Crear entrenamiento")).not_to_be_visible()
    expect(page).to_have_url(f"{app_url}/entrenamientos")


def test_admin_creates_training(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an admin on the creation page.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    page.goto(f"{app_url}/entrenamientos/nuevo")

    # When they fill the small form and submit.
    page.get_by_label("Título").fill("Fuerza máxima")
    page.get_by_label("Categoría").select_option(label="Gimnasio")
    page.get_by_label("Subtipo").select_option(label="Acumulación")
    page.get_by_role("button", name="Crear entrenamiento").click()

    # Then a success toast confirms it and they land on the new training's detail page.
    expect(page.get_by_role("status").filter(has_text="Entrenamiento creado.")).to_be_visible()
    expect(page).to_have_url(re.compile(rf"{re.escape(app_url)}/entrenamientos/[0-9a-f-]+$"))
    expect(page.get_by_role("heading", name="Fuerza máxima")).to_be_visible()


def test_subtype_options_adapt_to_category(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given the creation page.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    page.goto(f"{app_url}/entrenamientos/nuevo")

    subtype = page.get_by_label("Subtipo")

    # Subtype is disabled until a category is chosen.
    expect(subtype).to_be_disabled()

    # Choosing gym offers the gym subtypes.
    page.get_by_label("Categoría").select_option(label="Gimnasio")
    expect(subtype).to_be_enabled()
    expect(subtype.get_by_role("option", name="Adaptación")).to_be_attached()
    expect(subtype.get_by_role("option", name="Acumulación")).to_be_attached()
    # A pool subtype is not offered for gym.
    expect(subtype.get_by_role("option", name="Resistencia")).to_have_count(0)

    # Switching to pool swaps in the pool subtypes.
    page.get_by_label("Categoría").select_option(label="Piscina")
    expect(subtype.get_by_role("option", name="Resistencia")).to_be_attached()
    expect(subtype.get_by_role("option", name="Aláctico")).to_be_attached()
    expect(subtype.get_by_role("option", name="Adaptación")).to_have_count(0)


def test_switching_category_resets_subtype(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a category + subtype chosen.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    page.goto(f"{app_url}/entrenamientos/nuevo")
    page.get_by_label("Categoría").select_option(label="Gimnasio")
    page.get_by_label("Subtipo").select_option(label="Acumulación")

    # When the category changes, the previously selected subtype is cleared.
    page.get_by_label("Categoría").select_option(label="Piscina")
    expect(page.get_by_label("Subtipo")).to_have_value("")


def test_category_and_subtype_required(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given the creation page with nothing selected.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    page.goto(f"{app_url}/entrenamientos/nuevo")

    # When submitting empty.
    page.get_by_role("button", name="Crear entrenamiento").click()

    # Then client-side validation flags the required category.
    expect(page.get_by_text("La categoría es obligatoria")).to_be_visible()
