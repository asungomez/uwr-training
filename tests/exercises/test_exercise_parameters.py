from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import Exercise, ExerciseParameter, User


def test_detail_shows_parameters(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an exercise with two parameters (seeded directly).
    admin = create_user(role="admin", email="admin@example.com")
    exercise = create_exercise(
        name="Sentadilla",
        type="gym",
        parameters=[
            ExerciseParameter(name="Peso", description="En kilos"),
            ExerciseParameter(name="Tiempo"),
        ],
    )
    log_in_as(admin)

    # When the detail page loads.
    page.goto(f"{app_url}/ejercicios/{exercise.id}")

    # Then the parameters section lists both, with the description where present.
    section = page.get_by_role("list").filter(has_text="Peso")
    expect(page.get_by_role("heading", name="Parámetros")).to_be_visible()
    expect(section.get_by_text("Peso")).to_be_visible()
    expect(section.get_by_text("En kilos")).to_be_visible()
    expect(section.get_by_text("Tiempo")).to_be_visible()


def test_detail_hides_parameters_section_when_empty(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an exercise with no parameters.
    admin = create_user(role="admin", email="admin@example.com")
    exercise = create_exercise(name="Sentadilla", type="gym")
    log_in_as(admin)

    # When the detail page loads, the parameters section is not shown.
    page.goto(f"{app_url}/ejercicios/{exercise.id}")
    expect(page.get_by_role("heading", name="Sentadilla")).to_be_visible()
    expect(page.get_by_role("heading", name="Parámetros")).not_to_be_visible()


def test_admin_adds_parameters_when_creating(
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

    # When they fill the name and add a parameter with name + description.
    page.get_by_label("Nombre").fill("Press banca")
    page.get_by_role("button", name="Añadir parámetro").click()
    page.get_by_placeholder("Nombre (p. ej. Peso)").fill("Peso")
    page.get_by_placeholder("Descripción (opcional)…").fill("En kilos")
    page.get_by_role("button", name="Guardar ejercicio").click()

    # Then it's created and the parameter shows on its detail page.
    expect(page.get_by_role("status").filter(has_text="Ejercicio creado.")).to_be_visible()
    expect(page.get_by_role("heading", name="Press banca")).to_be_visible()
    expect(page.get_by_role("heading", name="Parámetros")).to_be_visible()
    expect(page.get_by_text("Peso")).to_be_visible()
    expect(page.get_by_text("En kilos")).to_be_visible()


def test_parameter_name_required_blocks_submit(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given the new-exercise page with a name filled.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    page.goto(f"{app_url}/ejercicios")
    page.get_by_role("link", name="Nuevo ejercicio").click()
    page.get_by_label("Nombre").fill("Press banca")

    # When I add a parameter but leave its name blank and submit.
    page.get_by_role("button", name="Añadir parámetro").click()
    page.get_by_role("button", name="Guardar ejercicio").click()

    # Then client-side validation flags the missing parameter name and no toast shows.
    expect(page.get_by_text("El nombre es obligatorio")).to_be_visible()
    expect(page.get_by_role("status").filter(has_text="Ejercicio creado.")).not_to_be_visible()


def test_edit_prefills_and_removes_parameter(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an exercise with a parameter.
    admin = create_user(role="admin", email="admin@example.com")
    create_exercise(
        name="Sentadilla",
        type="gym",
        parameters=[ExerciseParameter(name="Peso", description="En kilos")],
    )
    log_in_as(admin)
    page.goto(f"{app_url}/ejercicios")

    # When editing, the existing parameter is pre-filled.
    page.get_by_role("link", name="Editar Sentadilla").click()
    expect(page.get_by_placeholder("Nombre (p. ej. Peso)")).to_have_value("Peso")
    expect(page.get_by_placeholder("Descripción (opcional)…")).to_have_value("En kilos")

    # When I remove it and save.
    page.get_by_role("button", name="Quitar parámetro").click()
    page.get_by_role("button", name="Guardar ejercicio").click()

    # Then it lands on the detail page, which no longer shows a parameters section.
    expect(page.get_by_role("status").filter(has_text="Ejercicio actualizado.")).to_be_visible()
    expect(page.get_by_role("heading", name="Sentadilla")).to_be_visible()
    expect(page.get_by_role("heading", name="Parámetros")).not_to_be_visible()


def test_duplicate_parameter_name_shows_error(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given the new-exercise page with two parameters sharing a name.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    page.goto(f"{app_url}/ejercicios")
    page.get_by_role("link", name="Nuevo ejercicio").click()
    page.get_by_label("Nombre").fill("Press banca")

    page.get_by_role("button", name="Añadir parámetro").click()
    page.get_by_role("button", name="Añadir parámetro").click()
    names = page.get_by_placeholder("Nombre (p. ej. Peso)")
    names.nth(0).fill("Peso")
    names.nth(1).fill("Peso")
    page.get_by_role("button", name="Guardar ejercicio").click()

    # Then the API rejects it with the localized error.
    expect(page.get_by_role("alert")).to_have_text(
        "Algún parámetro no es válido (nombre vacío o repetido)."
    )
