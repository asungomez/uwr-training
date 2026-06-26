from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import Exercise, StrengthTestItem, User


def test_member_sees_no_edit_button(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)
    page.goto(f"{app_url}/pruebas/fuerza")
    expect(page.get_by_role("heading", name="Prueba de fuerza")).to_be_visible()
    expect(page.get_by_role("link", name="Editar")).to_have_count(0)


def test_member_cannot_access_edit_page(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)
    page.goto(f"{app_url}/pruebas/fuerza/editar")
    # AdminRoute redirects members away.
    expect(page).to_have_url(f"{app_url}/entrenamientos")


def test_admin_edits_strength_test(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    admin = create_user(role="admin", email="admin@example.com")
    create_exercise(name="Peso muerto", type="gym")
    log_in_as(admin)

    # From the info page, the admin opens the editor.
    page.goto(f"{app_url}/pruebas/fuerza")
    page.get_by_role("link", name="Editar").click()
    expect(page).to_have_url(f"{app_url}/pruebas/fuerza/editar")

    # Add an exercise (search → pick) and set its multiplier.
    page.get_by_role("button", name="Añadir ejercicio").click()
    page.get_by_placeholder("Buscar ejercicio…").fill("Peso muerto")
    page.get_by_role("button", name="Peso muerto").click()
    page.get_by_label("Multiplicador").fill("1.5")

    page.get_by_role("button", name="Guardar cambios").click()
    expect(
        page.get_by_role("status").filter(has_text="Prueba de fuerza actualizada.")
    ).to_be_visible()

    # Back on the info page, the exercise + multiplier are listed.
    expect(page).to_have_url(f"{app_url}/pruebas/fuerza")
    main = page.get_by_role("main")
    expect(main.get_by_text("Peso muerto")).to_be_visible()
    expect(main.get_by_text("×1.5")).to_be_visible()


def test_edit_page_preloads_existing_items(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_strength_test_item: Callable[..., StrengthTestItem],
    log_in_as: Callable[[User], None],
) -> None:
    admin = create_user(role="admin", email="admin@example.com")
    squat = create_exercise(name="Sentadilla", type="gym")
    create_strength_test_item(exercise_id=squat.id, weight_multiplier=2.0)
    log_in_as(admin)

    page.goto(f"{app_url}/pruebas/fuerza/editar")
    # The existing item is pre-loaded: exercise name shown, multiplier in the input.
    expect(page.get_by_text("Sentadilla")).to_be_visible()
    expect(page.get_by_label("Multiplicador")).to_have_value("2")
