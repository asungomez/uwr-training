from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import Exercise, User, Week, WeekRequirement


def test_speed_test_link_opens_explanation(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos")

    page.get_by_role("link", name="Prueba de velocidad").click()
    expect(page).to_have_url(f"{app_url}/pruebas/velocidad")

    main = page.get_by_role("main")
    expect(main.get_by_role("heading", name="Prueba de velocidad")).to_be_visible()
    expect(main.get_by_text("bajo el agua, con aletas", exact=False)).to_be_visible()
    # The scoring table is shown (a couple of the ratings).
    expect(main.get_by_role("table")).to_be_visible()
    expect(main.get_by_text("Tiempo objetivo", exact=False)).to_be_visible()
    expect(main.get_by_text("Muy bien", exact=False)).to_be_visible()


def test_member_sees_no_warmup_edit_button(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Members can't edit the warmup; only admins get the button. No log buttons either.
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)
    page.goto(f"{app_url}/pruebas/velocidad")

    main = page.get_by_role("main")
    expect(main.get_by_role("link", name="Editar calentamiento")).to_have_count(0)


def test_admin_edits_warmup_with_training_form(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    admin = create_user(role="admin", email="admin@example.com")
    create_exercise(name="Nado suave", type="pool")
    log_in_as(admin)

    # From the speed-test page, open the warmup editor (the standard training form).
    page.goto(f"{app_url}/pruebas/velocidad")
    page.get_by_role("link", name="Editar calentamiento").click()
    expect(page).to_have_url(f"{app_url}/pruebas/velocidad/editar-calentamiento")

    # Build a block with a pool exercise.
    page.get_by_label("Título").fill("Calentamiento velocidad")
    page.get_by_role("button", name="Añadir bloque").click()
    page.get_by_label("Nombre del bloque").fill("Activación")
    page.get_by_role("button", name="Añadir sub-bloque").click()
    page.get_by_label("Nombre del sub-bloque").fill("Series")
    page.get_by_role("button", name="Añadir ejercicio").click()
    page.get_by_placeholder("Buscar ejercicio…").fill("Nado")
    page.get_by_role("button", name="Nado suave").click()
    page.get_by_role("button", name="Guardar cambios").click()

    expect(
        page.get_by_role("status").filter(has_text="Calentamiento actualizado.")
    ).to_be_visible()
    expect(page).to_have_url(f"{app_url}/pruebas/velocidad")

    # The warmup isn't shown on the explanation page — it appears when starting the
    # test (the register page), read-only.
    page.goto(f"{app_url}/pruebas/velocidad/registrar")
    main = page.get_by_role("main")
    expect(main.get_by_role("heading", name="Activación")).to_be_visible()
    expect(main.get_by_text("Nado suave")).to_be_visible()

    # The warmup is a pool/endurance session, but it must NOT leak into the normal
    # pool trainings list.
    page.goto(f"{app_url}/entrenamientos/piscina/resistencia")
    expect(page.get_by_role("button", name="Calentamiento velocidad")).to_have_count(0)
    expect(page.get_by_text("Todavía no hay entrenamientos en este subtipo.")).to_be_visible()


def test_pool_exercise_search_offered_in_warmup(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # The warmup is a pool session, so its exercise picker offers pool, not gym.
    admin = create_user(role="admin", email="admin@example.com")
    create_exercise(name="Nado piscina", type="pool")
    create_exercise(name="Sentadilla gimnasio", type="gym")
    log_in_as(admin)

    page.goto(f"{app_url}/pruebas/velocidad/editar-calentamiento")
    page.get_by_role("button", name="Añadir bloque").click()
    page.get_by_label("Nombre del bloque").fill("B")
    page.get_by_role("button", name="Añadir sub-bloque").click()
    page.get_by_label("Nombre del sub-bloque").fill("S")
    page.get_by_role("button", name="Añadir ejercicio").click()
    page.get_by_placeholder("Buscar ejercicio…").fill("a")
    expect(page.get_by_role("button", name="Nado piscina")).to_be_visible()
    expect(page.get_by_role("button", name="Sentadilla gimnasio")).to_have_count(0)


def test_week_can_have_strength_and_speed_tests(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_week: Callable[..., Week],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    week = create_week(
        name="Semana con pruebas",
        phase="adaptation",
        requirements=[
            WeekRequirement(position=0, category="test", subtype="strength", count=1),
            WeekRequirement(position=1, category="test", subtype="speed", count=1),
        ],
    )
    log_in_as(member)
    page.goto(f"{app_url}/calendario/{week.id}")

    main = page.get_by_role("main")
    # Both tests are listed at 0/1 and link to their explanation pages.
    strength_link = main.get_by_role("link", name="Prueba · Fuerza")
    speed_link = main.get_by_role("link", name="Prueba · Velocidad")
    expect(strength_link).to_have_attribute("href", "/pruebas/fuerza")
    expect(speed_link).to_have_attribute("href", "/pruebas/velocidad")
    expect(main.get_by_text("0/1", exact=True)).to_have_count(2)


def test_admin_adds_speed_test_without_sessions_count(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    page.goto(f"{app_url}/calendario/nueva")

    page.get_by_label("Nombre").fill("Semana velocidad")
    page.get_by_role("button", name="Añadir sesión").click()

    # Prueba category offers Velocidad and hides the count input.
    page.get_by_label("Categoría").select_option(label="Prueba")
    subtype = page.get_by_label("Subtipo")
    expect(subtype.get_by_role("option", name="Velocidad")).to_be_attached()
    expect(page.get_by_label("Sesiones")).to_have_count(0)
    subtype.select_option(label="Velocidad")

    page.get_by_role("button", name="Crear semana").click()
    expect(page.get_by_role("status").filter(has_text="Semana creada.")).to_be_visible()

    main = page.get_by_role("main")
    test_link = main.get_by_role("link", name="Prueba · Velocidad")
    expect(test_link).to_have_attribute("href", "/pruebas/velocidad")
    expect(main.get_by_text("0/1", exact=True)).to_be_visible()
