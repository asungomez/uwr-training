from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import Exercise, ExerciseGymMaterial, GymMaterial, User


def _with_material(name: str) -> ExerciseGymMaterial:
    return ExerciseGymMaterial(gym_material=GymMaterial(name=name), position=0)


def test_detail_shows_materials(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an exercise with a material (seeded directly).
    admin = create_user(role="admin", email="admin@example.com")
    exercise = create_exercise(
        name="Sentadilla", type="gym", gym_materials=[_with_material("Mancuernas")]
    )
    log_in_as(admin)

    page.goto(f"{app_url}/ejercicios/{exercise.id}")
    expect(page.get_by_role("heading", name="Materiales")).to_be_visible()
    expect(page.get_by_text("Mancuernas")).to_be_visible()


def test_detail_hides_materials_section_when_empty(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    admin = create_user(role="admin", email="admin@example.com")
    exercise = create_exercise(name="Sentadilla", type="gym")
    log_in_as(admin)

    page.goto(f"{app_url}/ejercicios/{exercise.id}")
    expect(page.get_by_role("heading", name="Sentadilla")).to_be_visible()
    expect(page.get_by_role("heading", name="Materiales")).not_to_be_visible()


def test_admin_adds_a_new_material_when_creating(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an admin on the new-exercise page.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    page.goto(f"{app_url}/ejercicios")
    page.get_by_role("link", name="Nuevo ejercicio").click()

    # When they type a material name and add it (creating it on save).
    page.get_by_label("Nombre", exact=True).fill("Press de banca")
    page.get_by_label("Material", exact=True).fill("Banco plano")
    page.get_by_role("button", name="Añadir material").click()
    page.get_by_role("button", name="Guardar ejercicio").click()

    # Then it's created and the material shows on its detail page.
    expect(page.get_by_role("status").filter(has_text="Ejercicio creado.")).to_be_visible()
    expect(page.get_by_role("heading", name="Materiales")).to_be_visible()
    expect(page.get_by_text("Banco plano")).to_be_visible()


def test_existing_material_is_suggested_and_reused(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an existing exercise already using a material.
    admin = create_user(role="admin", email="admin@example.com")
    create_exercise(name="Sentadilla", type="gym", gym_materials=[_with_material("Mancuernas")])
    log_in_as(admin)
    page.goto(f"{app_url}/ejercicios")
    page.get_by_role("link", name="Nuevo ejercicio").click()

    # When I start typing its name, it's suggested; selecting it adds the chip.
    page.get_by_label("Nombre", exact=True).fill("Curl de bíceps")
    page.get_by_label("Material", exact=True).fill("Mancu")
    page.get_by_role("button", name="Mancuernas").click()
    page.get_by_role("button", name="Guardar ejercicio").click()

    # Then the new exercise also shows the material.
    expect(page.get_by_role("status").filter(has_text="Ejercicio creado.")).to_be_visible()
    expect(page.get_by_role("heading", name="Materiales")).to_be_visible()
    expect(page.get_by_text("Mancuernas")).to_be_visible()


def test_edit_prefills_and_removes_material(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    admin = create_user(role="admin", email="admin@example.com")
    create_exercise(name="Sentadilla", type="gym", gym_materials=[_with_material("Mancuernas")])
    log_in_as(admin)
    page.goto(f"{app_url}/ejercicios")

    # The material chip is pre-filled when editing.
    page.get_by_role("link", name="Editar Sentadilla").click()
    expect(page.get_by_text("Mancuernas")).to_be_visible()

    # Removing it and saving drops the materials section from the detail page.
    page.get_by_role("button", name="Quitar Mancuernas").click()
    page.get_by_role("button", name="Guardar ejercicio").click()
    expect(page.get_by_role("status").filter(has_text="Ejercicio actualizado.")).to_be_visible()
    expect(page.get_by_role("heading", name="Materiales")).not_to_be_visible()
