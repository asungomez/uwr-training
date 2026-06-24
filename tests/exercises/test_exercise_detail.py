from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import Exercise, User


def test_card_navigates_to_detail(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an exercise.
    admin = create_user(role="admin", email="admin@example.com")
    exercise = create_exercise(name="Sentadilla", description="Piernas", type="gym")
    log_in_as(admin)
    page.goto(f"{app_url}/ejercicios")

    # When I click its card.
    page.get_by_role("heading", name="Sentadilla").click()

    # Then I land on the detail page showing name, type and description.
    expect(page).to_have_url(f"{app_url}/ejercicios/{exercise.id}")
    # The breadcrumb is detail-only, so waiting on it confirms the route swapped.
    expect(page.get_by_label("Migas de pan")).to_be_visible()
    expect(page.get_by_role("heading", name="Sentadilla")).to_be_visible()
    expect(page.get_by_text("Piernas")).to_be_visible()


def test_detail_shows_placeholder_without_description(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an exercise with no description.
    admin = create_user(role="admin", email="admin@example.com")
    exercise = create_exercise(name="Dominadas", description=None, type="gym")
    log_in_as(admin)

    # When I open its detail page.
    page.goto(f"{app_url}/ejercicios/{exercise.id}")

    # Then a placeholder stands in for the missing description.
    expect(page.get_by_text("Sin descripción.")).to_be_visible()


def test_breadcrumb_returns_to_list(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # Given the detail page of an exercise.
    admin = create_user(role="admin", email="admin@example.com")
    exercise = create_exercise(name="Apnea", type="pool")
    log_in_as(admin)
    page.goto(f"{app_url}/ejercicios/{exercise.id}")

    # When I click the breadcrumb back to the list.
    page.get_by_label("Migas de pan").get_by_role("link", name="Ejercicios").click()

    # Then I'm on the list.
    expect(page).to_have_url(f"{app_url}/ejercicios")
    expect(page.get_by_role("heading", name="Ejercicios")).to_be_visible()


def test_admin_edits_from_detail(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # Given the detail page of an exercise.
    admin = create_user(role="admin", email="admin@example.com")
    exercise = create_exercise(name="Press banca", description="Pecho", type="gym")
    log_in_as(admin)
    page.goto(f"{app_url}/ejercicios/{exercise.id}")

    # When I edit it (the form is pre-populated).
    page.get_by_role("link", name="Editar").click()
    name = page.get_by_label("Nombre")
    expect(name).to_have_value("Press banca")
    name.fill("Press inclinado")
    page.get_by_role("button", name="Guardar ejercicio").click()

    # Then a toast confirms it and the header updates live.
    expect(page.get_by_role("status").filter(has_text="Ejercicio actualizado.")).to_be_visible()
    expect(page.get_by_role("heading", name="Press inclinado")).to_be_visible()


def test_admin_deletes_from_detail(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # Given the detail page of an exercise.
    admin = create_user(role="admin", email="admin@example.com")
    exercise = create_exercise(name="Zancadas", type="gym")
    log_in_as(admin)
    page.goto(f"{app_url}/ejercicios/{exercise.id}")

    # When I delete it and confirm.
    page.get_by_role("button", name="Eliminar").click()
    dialog = page.get_by_role("dialog", name="Eliminar ejercicio")
    expect(dialog).to_be_visible()
    dialog.get_by_role("button", name="Eliminar").click()

    # Then a toast confirms it and I'm sent back to the list.
    expect(page.get_by_role("status").filter(has_text="Ejercicio eliminado.")).to_be_visible()
    expect(page).to_have_url(f"{app_url}/ejercicios")
    expect(page.get_by_role("heading", name="Zancadas")).not_to_be_visible()


def test_member_sees_no_edit_or_delete_on_detail(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an exercise and a logged-in member.
    exercise = create_exercise(name="Buceo", description="Bajo el agua", type="pool")
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)

    # When the member opens the detail page.
    page.goto(f"{app_url}/ejercicios/{exercise.id}")

    # Then they see the details but no admin controls.
    expect(page.get_by_role("heading", name="Buceo")).to_be_visible()
    expect(page.get_by_role("button", name="Editar")).not_to_be_visible()
    expect(page.get_by_role("button", name="Eliminar")).not_to_be_visible()
