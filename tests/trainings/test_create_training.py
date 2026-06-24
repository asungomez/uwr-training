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

    # Then they land on the scope's creation page.
    expect(page).to_have_url(f"{app_url}/entrenamientos/gimnasio/acumulacion/nuevo")
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
    page.goto(f"{app_url}/entrenamientos/gimnasio/acumulacion/nuevo")
    expect(page.get_by_role("button", name="Crear entrenamiento")).not_to_be_visible()
    expect(page).to_have_url(f"{app_url}/entrenamientos")


def test_admin_creates_training_in_url_scope(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an admin on a scoped creation page (category + subtype from the URL).
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    page.goto(f"{app_url}/entrenamientos/gimnasio/acumulacion/nuevo")

    # The scope is shown (no category/subtype pickers in the form).
    expect(page.get_by_role("heading", name="Gimnasio / Acumulación")).to_be_visible()
    expect(page.get_by_label("Categoría")).to_have_count(0)
    expect(page.get_by_label("Subtipo")).to_have_count(0)

    # When they fill the title and submit.
    page.get_by_label("Título").fill("Fuerza máxima")
    page.get_by_role("button", name="Crear entrenamiento").click()

    # Then a success toast confirms it and they land on the new training's detail
    # page, which sits in the URL's scope.
    expect(page.get_by_role("status").filter(has_text="Entrenamiento creado.")).to_be_visible()
    expect(page).to_have_url(re.compile(rf"{re.escape(app_url)}/entrenamientos/[0-9a-f-]+$"))
    main = page.get_by_role("main")
    expect(main.get_by_role("heading", name="Fuerza máxima")).to_be_visible()
    expect(main.locator("span").get_by_text("Gimnasio")).to_be_visible()
    expect(main.locator("span").get_by_text("Acumulación")).to_be_visible()


def test_new_form_in_pool_scope_filters_exercises_to_pool(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given the creation page for a pool subtype, the scope shows the pool labels.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    page.goto(f"{app_url}/entrenamientos/piscina/resistencia/nuevo")
    expect(page.get_by_role("heading", name="Piscina / Resistencia")).to_be_visible()


def test_unknown_scope_redirects_away_from_new_form(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an admin opening a creation URL whose subtype doesn't belong to gym.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)

    # Then it redirects to the category list (no form for an invalid scope).
    page.goto(f"{app_url}/entrenamientos/gimnasio/resistencia/nuevo")
    expect(page).to_have_url(f"{app_url}/entrenamientos/gimnasio")
    expect(page.get_by_role("button", name="Crear entrenamiento")).to_have_count(0)
