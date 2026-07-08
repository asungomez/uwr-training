import re
from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import Exercise, User, Week, WeekRequirement


def test_lactic_acid_test_link_opens_explanation(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos")

    page.get_by_role("link", name="Prueba de ácido láctico").click()
    expect(page).to_have_url(f"{app_url}/pruebas/acido-lactico")

    main = page.get_by_role("main")
    expect(main.get_by_role("heading", name="Prueba de ácido láctico")).to_be_visible()
    expect(
        main.get_by_text("Las pruebas de ácido láctico se hacen en piscina", exact=False)
    ).to_be_visible()
    # The description mentions the personal best (in the second paragraph).
    expect(
        main.get_by_text("Se guardará ese valor como la marca personal", exact=False)
    ).to_be_visible()


def test_member_sees_no_warmup_edit_button(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Members can't edit the warmup; only admins get the button.
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)
    page.goto(f"{app_url}/pruebas/acido-lactico")

    main = page.get_by_role("main")
    expect(main.get_by_role("link", name="Editar calentamiento")).to_have_count(0)


def test_empezar_prueba_opens_register_page(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # "Empezar prueba" leads to the register page with breadcrumbs, title, and the
    # warmup shown read-only. Seed the warmup so a block is visible there.
    admin = create_user(role="admin", email="admin@example.com")
    create_exercise(name="Nado suave", type="pool")
    log_in_as(admin)

    page.goto(f"{app_url}/pruebas/acido-lactico/editar-calentamiento")
    page.get_by_label("Título").fill("Calentamiento ácido láctico")
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

    # From the explanation page, "Empezar prueba" navigates to /registrar.
    page.goto(f"{app_url}/pruebas/acido-lactico")
    page.get_by_role("link", name="Empezar prueba").click()
    expect(page).to_have_url(f"{app_url}/pruebas/acido-lactico/registrar")

    main = page.get_by_role("main")
    expect(main.get_by_role("heading", name="Registrar prueba de ácido láctico")).to_be_visible()
    # Breadcrumb back to the explanation page.
    expect(main.get_by_role("link", name="Prueba de ácido láctico")).to_have_attribute(
        "href", "/pruebas/acido-lactico"
    )
    # The warmup is shown read-only.
    expect(main.get_by_role("heading", name="Activación")).to_be_visible()
    expect(main.get_by_text("Nado suave")).to_be_visible()


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

    # From the lactic-acid-test page, open the warmup editor (standard training form).
    page.goto(f"{app_url}/pruebas/acido-lactico")
    page.get_by_role("link", name="Editar calentamiento").click()
    expect(page).to_have_url(f"{app_url}/pruebas/acido-lactico/editar-calentamiento")

    # Build a block with a pool exercise.
    page.get_by_label("Título").fill("Calentamiento ácido láctico")
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
    expect(page).to_have_url(f"{app_url}/pruebas/acido-lactico")

    # The warmup is shown read-only on the explanation page (below the description).
    main = page.get_by_role("main")
    expect(main.get_by_role("heading", name="Activación")).to_be_visible()
    expect(main.get_by_text("Nado suave")).to_be_visible()

    # The warmup is a pool session, but it must NOT leak into the normal pool
    # trainings list.
    page.goto(f"{app_url}/entrenamientos/piscina/alactico")
    expect(page.get_by_role("button", name="Calentamiento ácido láctico")).to_have_count(0)


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

    page.goto(f"{app_url}/pruebas/acido-lactico/editar-calentamiento")
    page.get_by_role("button", name="Añadir bloque").click()
    page.get_by_label("Nombre del bloque").fill("B")
    page.get_by_role("button", name="Añadir sub-bloque").click()
    page.get_by_label("Nombre del sub-bloque").fill("S")
    page.get_by_role("button", name="Añadir ejercicio").click()
    page.get_by_placeholder("Buscar ejercicio…").fill("a")
    expect(page.get_by_role("button", name="Nado piscina")).to_be_visible()
    expect(page.get_by_role("button", name="Sentadilla gimnasio")).to_have_count(0)


def test_both_warmups_coexist(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # Speed and lactic-acid warmups are both pool sessions at position -1; they must
    # NOT collide on the (category, subtype, position) uniqueness constraint.
    admin = create_user(role="admin", email="admin@example.com")
    create_exercise(name="Nado suave", type="pool")
    log_in_as(admin)

    # Edit the speed-test warmup first.
    page.goto(f"{app_url}/pruebas/velocidad/editar-calentamiento")
    page.get_by_label("Título").fill("Calentamiento velocidad")
    page.get_by_role("button", name="Guardar cambios").click()
    expect(
        page.get_by_role("status").filter(has_text="Calentamiento actualizado.")
    ).to_be_visible()

    # Then the lactic-acid warmup: loads without error and saves independently.
    page.goto(f"{app_url}/pruebas/acido-lactico/editar-calentamiento")
    expect(page.get_by_text("No se ha podido cargar el calentamiento.")).to_have_count(0)
    page.get_by_label("Título").fill("Calentamiento ácido láctico")
    page.get_by_role("button", name="Guardar cambios").click()
    expect(
        page.get_by_role("status").filter(has_text="Calentamiento actualizado.")
    ).to_be_visible()


def test_register_form_shows_both_fields_with_explanations(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # The register form has the two measures, each with its explanation paragraph.
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)
    page.goto(f"{app_url}/pruebas/acido-lactico/registrar")

    main = page.get_by_role("main")
    expect(main.get_by_role("heading", name="Marca personal")).to_be_visible()
    expect(main.get_by_text("del ejercicio llamado", exact=False)).to_be_visible()
    expect(main.get_by_role("heading", name="Resultado de la prueba")).to_be_visible()
    expect(main.get_by_text("8 veces en ciclos de 60 segundos", exact=False)).to_be_visible()
    expect(main.get_by_label("Marca personal en segundos")).to_be_visible()
    expect(main.get_by_label("Resultado en segundos")).to_be_visible()


def test_register_requires_at_least_one_field(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Submitting with both fields empty is rejected client-side; nothing is saved.
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)
    page.goto(f"{app_url}/pruebas/acido-lactico/registrar")

    page.get_by_role("button", name="Finalizar prueba").click()
    expect(page.get_by_text("Introduce al menos una de las dos marcas.")).to_be_visible()
    # Still on the register page (no navigation on a rejected submit).
    expect(page).to_have_url(f"{app_url}/pruebas/acido-lactico/registrar")


def test_register_saves_both_measures(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Filling both fields saves both logs and returns to the explanation page.
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)
    page.goto(f"{app_url}/pruebas/acido-lactico/registrar")

    page.get_by_label("Marca personal en segundos").fill("40.5")
    page.get_by_label("Resultado en segundos").fill("44.5")
    page.get_by_role("button", name="Finalizar prueba").click()

    expect(page.get_by_role("status").filter(has_text="Prueba registrada.")).to_be_visible()
    expect(page).to_have_url(f"{app_url}/pruebas/acido-lactico")


def test_register_only_one_measure_counts_towards_week(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_week: Callable[..., Week],
    log_in_as: Callable[[User], None],
) -> None:
    # A lactic-acid log linked to a week fills that week's test/lactic requirement,
    # and the calendar links back to the log's detail page.
    member = create_user(role="member", email="member@example.com")
    week = create_week(
        name="Semana con láctico",
        phase="adaptation",
        requirements=[WeekRequirement(position=0, category="test", subtype="lactic", count=1)],
    )
    log_in_as(member)

    page.goto(f"{app_url}/pruebas/acido-lactico/registrar")
    # The week is offered and pre-selected as recommended isn't guaranteed, so pick it.
    page.get_by_label("Semana").select_option(label="Semana con láctico")
    page.get_by_label("Resultado en segundos").fill("44.5")
    page.get_by_role("button", name="Finalizar prueba").click()
    expect(page.get_by_role("status").filter(has_text="Prueba registrada.")).to_be_visible()

    # The calendar shows the requirement completed, linking to the result detail.
    page.goto(f"{app_url}/calendario/{week.id}")
    main = page.get_by_role("main")
    expect(main.get_by_text("1/1", exact=True)).to_be_visible()
    result_link = main.get_by_role("link", name="Prueba de ácido láctico (resultado)")
    expect(result_link).to_be_visible()
    result_link.click()
    expect(page).to_have_url(re.compile(r"/pruebas/acido-lactico/registros/resultado/"))
    expect(page.get_by_role("main").get_by_text("44.5 s", exact=False)).to_be_visible()


def test_week_can_recommend_lactic_test(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Admin can add a Prueba · Ácido láctico requirement when creating a week.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    page.goto(f"{app_url}/calendario/nueva")

    page.get_by_label("Nombre").fill("Semana láctico")
    page.get_by_role("button", name="Añadir sesión").click()
    page.get_by_label("Categoría").select_option(label="Prueba")
    subtype = page.get_by_label("Subtipo")
    expect(subtype.get_by_role("option", name="Ácido láctico")).to_be_attached()
    subtype.select_option(label="Ácido láctico")

    page.get_by_role("button", name="Crear semana").click()
    expect(page.get_by_role("status").filter(has_text="Semana creada.")).to_be_visible()

    main = page.get_by_role("main")
    test_link = main.get_by_role("link", name="Prueba · Ácido láctico")
    expect(test_link).to_have_attribute("href", "/pruebas/acido-lactico")


def test_test_result_table_warns_without_personal_best(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # The test-result tab needs a personal best to build its scale; without one it
    # shows a warning instead of a table.
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)
    page.goto(f"{app_url}/pruebas/acido-lactico")

    main = page.get_by_role("main")
    # The test-result tab is selected by default.
    expect(main.get_by_role("tab", name="Prueba de ácido láctico")).to_have_attribute(
        "aria-selected", "true"
    )
    expect(
        main.get_by_text(
            "Hace falta algún resultado de marca personal para poder valorar", exact=False
        )
    ).to_be_visible()


def test_test_result_table_computed_from_last_personal_best(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_lactic_acid_personal_best_log: Callable[..., object],
    log_in_as: Callable[[User], None],
) -> None:
    # With a personal best of 40 s, the scale is pb + offset: 43 → Leyenda, the
    # 44.5-45 objetivo band, up to 49 → the worst rating.
    member = create_user(role="member", email="member@example.com")
    create_lactic_acid_personal_best_log(athlete_id=member.id, seconds=40.0)
    log_in_as(member)
    page.goto(f"{app_url}/pruebas/acido-lactico")

    main = page.get_by_role("main")
    expect(main.get_by_text("a partir de tu última marca personal (40 s)", exact=False)).to_be_visible()
    table = main.get_by_role("table")
    expect(table.get_by_text("43 s", exact=True)).to_be_visible()  # pb + 3 → Leyenda
    expect(table.get_by_text("44.5 - 45 s", exact=True)).to_be_visible()  # objetivo band
    expect(table.get_by_text("49 s", exact=True)).to_be_visible()  # pb + 9 → worst
    expect(table.get_by_text("Objetivo", exact=True)).to_be_visible()
    expect(table.get_by_text("Leyenda", exact=True)).to_be_visible()


def test_personal_best_tab_shows_placeholder_table(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Switching to the personal-best tab shows the (placeholder) hardcoded table.
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)
    page.goto(f"{app_url}/pruebas/acido-lactico")

    main = page.get_by_role("main")
    main.get_by_role("tab", name="Marca personal").click()
    table = main.get_by_role("table")
    expect(table).to_be_visible()
    # All the rating rows are present.
    for rating in ("Leyenda", "Muy bien", "Bien", "Objetivo", "Cari cómo te lo digo"):
        expect(table.get_by_text(rating, exact=True)).to_be_visible()
