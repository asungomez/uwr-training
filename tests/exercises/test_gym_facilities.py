from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import Exercise, ExerciseGymFacility, GymFacility, User


def _with_facility(name: str) -> ExerciseGymFacility:
    return ExerciseGymFacility(gym_facility=GymFacility(name=name), position=0)


def test_detail_shows_facilities(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    admin = create_user(role="admin", email="admin@example.com")
    exercise = create_exercise(
        name="Dominadas", type="gym", gym_facilities=[_with_facility("Barra de dominadas")]
    )
    log_in_as(admin)

    page.goto(f"{app_url}/ejercicios/{exercise.id}")
    expect(page.get_by_role("heading", name="Instalaciones")).to_be_visible()
    expect(page.get_by_text("Barra de dominadas")).to_be_visible()


def test_detail_hides_facilities_section_when_empty(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    admin = create_user(role="admin", email="admin@example.com")
    exercise = create_exercise(name="Dominadas", type="gym")
    log_in_as(admin)

    page.goto(f"{app_url}/ejercicios/{exercise.id}")
    expect(page.get_by_role("heading", name="Dominadas")).to_be_visible()
    expect(page.get_by_role("heading", name="Instalaciones")).not_to_be_visible()


def test_admin_adds_a_new_facility_when_creating(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    page.goto(f"{app_url}/ejercicios")
    page.get_by_role("link", name="Nuevo ejercicio").click()

    # Type a facility name and add it (creating it on save).
    page.get_by_label("Nombre", exact=True).fill("Remo")
    page.get_by_label("Instalación", exact=True).fill("Máquina de remo")
    page.get_by_role("button", name="Añadir instalación").click()
    page.get_by_role("button", name="Guardar ejercicio").click()

    expect(page.get_by_role("status").filter(has_text="Ejercicio creado.")).to_be_visible()
    expect(page.get_by_role("heading", name="Instalaciones")).to_be_visible()
    expect(page.get_by_text("Máquina de remo")).to_be_visible()


def test_existing_facility_is_suggested_and_reused(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    admin = create_user(role="admin", email="admin@example.com")
    create_exercise(
        name="Dominadas", type="gym", gym_facilities=[_with_facility("Barra de dominadas")]
    )
    log_in_as(admin)
    page.goto(f"{app_url}/ejercicios")
    page.get_by_role("link", name="Nuevo ejercicio").click()

    page.get_by_label("Nombre", exact=True).fill("Remo con barra")
    page.get_by_label("Instalación", exact=True).fill("Barra")
    page.get_by_role("button", name="Barra de dominadas").click()
    page.get_by_role("button", name="Guardar ejercicio").click()

    expect(page.get_by_role("status").filter(has_text="Ejercicio creado.")).to_be_visible()
    expect(page.get_by_role("heading", name="Instalaciones")).to_be_visible()
    expect(page.get_by_text("Barra de dominadas")).to_be_visible()


def test_edit_prefills_and_removes_facility(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    admin = create_user(role="admin", email="admin@example.com")
    create_exercise(
        name="Dominadas", type="gym", gym_facilities=[_with_facility("Barra de dominadas")]
    )
    log_in_as(admin)
    page.goto(f"{app_url}/ejercicios")

    page.get_by_role("link", name="Editar Dominadas").click()
    expect(page.get_by_text("Barra de dominadas")).to_be_visible()

    page.get_by_role("button", name="Quitar Barra de dominadas").click()
    page.get_by_role("button", name="Guardar ejercicio").click()
    expect(page.get_by_role("status").filter(has_text="Ejercicio actualizado.")).to_be_visible()
    expect(page.get_by_role("heading", name="Instalaciones")).not_to_be_visible()
