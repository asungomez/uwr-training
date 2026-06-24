import re
from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import TrainingCategory, TrainingSubtype, User, Week, WeekRequirement


def _week_with_requirements(create_week: Callable[..., Week]) -> Week:
    """A week matching the user's example: 2 pool/endurance, 2 gym/adaptation,
    1 cardio/anaerobic."""
    return create_week(
        name="Semana 1",
        recommended_date="Semana del 3 de marzo",
        phase="adaptation",
        requirements=[
            WeekRequirement(
                position=0,
                category=TrainingCategory.pool,
                subtype=TrainingSubtype.endurance,
                count=2,
            ),
            WeekRequirement(
                position=1,
                category=TrainingCategory.gym,
                subtype=TrainingSubtype.adaptation,
                count=2,
            ),
            WeekRequirement(
                position=2,
                category=TrainingCategory.cardio,
                subtype=TrainingSubtype.anaerobic,
                count=1,
            ),
        ],
    )


def test_sidebar_has_calendar_link(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos")
    expect(page.get_by_role("link", name="Calendario").first).to_be_visible()


def test_list_shows_weeks_in_order(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_week: Callable[..., Week],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    create_week(name="Primera", phase="adaptation")
    create_week(name="Segunda", phase="accumulation")
    log_in_as(member)
    page.goto(f"{app_url}/calendario")

    rows = page.get_by_role("listitem")
    expect(rows).to_have_count(2)
    expect(rows.nth(0)).to_contain_text("Primera")
    expect(rows.nth(1)).to_contain_text("Segunda")


def test_detail_shows_requirements(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_week: Callable[..., Week],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    week = _week_with_requirements(create_week)
    log_in_as(member)
    page.goto(f"{app_url}/calendario/{week.id}")

    main = page.get_by_role("main")
    expect(main.get_by_role("heading", name="Semana 1")).to_be_visible()
    expect(main.get_by_text("Semana del 3 de marzo")).to_be_visible()
    expect(main.get_by_text("Piscina · Resistencia")).to_be_visible()
    expect(main.get_by_text("Gimnasio · Adaptación")).to_be_visible()
    expect(main.get_by_text("Cardio · Anaeróbico")).to_be_visible()
    expect(main.get_by_text("1 sesión", exact=True)).to_be_visible()


def test_admin_creates_week(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    page.goto(f"{app_url}/calendario")

    page.get_by_role("link", name="Nueva semana").click()
    expect(page).to_have_url(f"{app_url}/calendario/nueva")

    page.get_by_label("Nombre").fill("Semana inicial")
    page.get_by_label("Fecha recomendada").fill("Primera semana")
    page.get_by_label("Fase del mesociclo").select_option(label="Acumulación")

    page.get_by_role("button", name="Añadir sesión").click()
    page.get_by_label("Categoría").select_option(label="Piscina")
    page.get_by_label("Subtipo").select_option(label="Resistencia")
    page.get_by_label("Sesiones").fill("3")

    page.get_by_role("button", name="Crear semana").click()

    expect(page.get_by_role("status").filter(has_text="Semana creada.")).to_be_visible()
    expect(page).to_have_url(re.compile(rf"{re.escape(app_url)}/calendario/[0-9a-f-]+$"))
    main = page.get_by_role("main")
    expect(main.get_by_role("heading", name="Semana inicial")).to_be_visible()
    expect(main.get_by_text("Piscina · Resistencia")).to_be_visible()
    expect(main.get_by_text("3 sesiones")).to_be_visible()


def test_subtype_options_depend_on_category(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    page.goto(f"{app_url}/calendario/nueva")
    page.get_by_role("button", name="Añadir sesión").click()

    subtype = page.get_by_label("Subtipo")
    expect(subtype).to_be_disabled()

    page.get_by_label("Categoría").select_option(label="Gimnasio")
    expect(subtype).to_be_enabled()
    expect(subtype.get_by_role("option", name="Adaptación")).to_be_attached()
    expect(subtype.get_by_role("option", name="Resistencia")).to_have_count(0)


def test_admin_edits_week(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_week: Callable[..., Week],
    log_in_as: Callable[[User], None],
) -> None:
    admin = create_user(role="admin", email="admin@example.com")
    week = _week_with_requirements(create_week)
    log_in_as(admin)
    page.goto(f"{app_url}/calendario/{week.id}/editar")

    expect(page.get_by_label("Nombre")).to_have_value("Semana 1")
    expect(page.get_by_label("Fecha recomendada")).to_have_value("Semana del 3 de marzo")

    page.get_by_label("Nombre").fill("Semana renombrada")
    page.get_by_role("button", name="Guardar cambios").click()

    expect(page.get_by_role("status").filter(has_text="Semana actualizada.")).to_be_visible()
    expect(page).to_have_url(f"{app_url}/calendario/{week.id}")
    expect(page.get_by_role("main").get_by_role("heading", name="Semana renombrada")).to_be_visible()


def test_admin_deletes_week(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_week: Callable[..., Week],
    log_in_as: Callable[[User], None],
) -> None:
    admin = create_user(role="admin", email="admin@example.com")
    week = create_week(name="A borrar", phase="adaptation")
    log_in_as(admin)
    page.goto(f"{app_url}/calendario/{week.id}")

    page.get_by_role("button", name="Eliminar").click()
    dialog = page.get_by_role("dialog", name="Eliminar semana")
    expect(dialog).to_be_visible()
    dialog.get_by_role("button", name="Eliminar").click()

    expect(page.get_by_role("status").filter(has_text="Semana eliminada.")).to_be_visible()
    expect(page).to_have_url(f"{app_url}/calendario")
    expect(page.get_by_text("Todavía no hay semanas.")).to_be_visible()


def test_member_sees_no_admin_controls(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_week: Callable[..., Week],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    week = create_week(name="Solo lectura", phase="adaptation")
    log_in_as(member)

    # No create button on the list.
    page.goto(f"{app_url}/calendario")
    expect(page.get_by_role("link", name="Nueva semana")).not_to_be_visible()

    # No edit/delete on the detail.
    page.goto(f"{app_url}/calendario/{week.id}")
    expect(page.get_by_role("main").get_by_role("heading", name="Solo lectura")).to_be_visible()
    expect(page.get_by_role("link", name="Editar")).not_to_be_visible()
    expect(page.get_by_role("button", name="Eliminar")).not_to_be_visible()


def test_member_cannot_access_new_or_edit(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_week: Callable[..., Week],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    week = create_week(name="Semana", phase="adaptation")
    log_in_as(member)

    page.goto(f"{app_url}/calendario/nueva")
    expect(page.get_by_role("button", name="Crear semana")).not_to_be_visible()
    expect(page).to_have_url(f"{app_url}/entrenamientos")

    page.goto(f"{app_url}/calendario/{week.id}/editar")
    expect(page.get_by_role("button", name="Guardar cambios")).not_to_be_visible()
    expect(page).to_have_url(f"{app_url}/entrenamientos")
