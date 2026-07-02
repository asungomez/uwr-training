from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from playwright.sync_api import Page, expect

from app.models import (
    BodyweightLog,
    Exercise,
    StrengthTestItem,
    StrengthTestLog,
    User,
)


def test_sidebar_has_pruebas_section(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos")

    nav = page.get_by_role("navigation").first
    expect(nav.get_by_text("Pruebas", exact=True)).to_be_visible()
    # Both tests are now real links under the Pruebas section.
    expect(nav.get_by_role("link", name="Prueba de fuerza")).to_be_visible()
    expect(nav.get_by_role("link", name="Prueba de velocidad")).to_be_visible()


def test_strength_test_link_opens_explanation(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos")

    page.get_by_role("link", name="Prueba de fuerza").click()
    expect(page).to_have_url(f"{app_url}/pruebas/fuerza")

    main = page.get_by_role("main")
    expect(main.get_by_role("heading", name="Prueba de fuerza")).to_be_visible()
    expect(main.get_by_text("guiar el esfuerzo necesario", exact=False)).to_be_visible()
    expect(main.get_by_text("último peso corporal registrado", exact=False)).to_be_visible()


def test_register_warns_when_no_bodyweight(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)

    page.goto(f"{app_url}/pruebas/fuerza")
    page.get_by_role("link", name="Hacer prueba").click()
    expect(page).to_have_url(f"{app_url}/pruebas/fuerza/registrar")

    # No body-weight register → a warning, no reference weight, and a shortcut to register.
    main = page.get_by_role("main")
    expect(main.get_by_text("al menos un registro de peso", exact=False)).to_be_visible()
    expect(main.get_by_role("link", name="Registrar peso")).to_be_visible()
    expect(main.get_by_text("Peso corporal de referencia", exact=False)).to_have_count(0)


def test_register_shows_reference_bodyweight(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_bodyweight_log: Callable[..., BodyweightLog],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    create_bodyweight_log(athlete_id=member.id, weight_kg=72.5)
    log_in_as(member)

    page.goto(f"{app_url}/pruebas/fuerza/registrar")
    main = page.get_by_role("main")
    # With a body weight (but no exercises configured here), the reference weight shows
    # and there's no missing-bodyweight warning. The populated form is covered in
    # test_strength_test_log.py.
    expect(main.get_by_text("72.5 kg", exact=False)).to_be_visible()
    expect(main.get_by_text("todavía no tiene ejercicios", exact=False)).to_be_visible()
    expect(main.get_by_text("al menos un registro de peso", exact=False)).to_have_count(0)


def test_page_shows_per_exercise_graphs_with_target(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_bodyweight_log: Callable[..., BodyweightLog],
    create_strength_test_item: Callable[..., StrengthTestItem],
    create_strength_test_log: Callable[..., StrengthTestLog],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a test with two exercises, a body weight, and two results each.
    member = create_user(role="member", email="member@example.com")
    squat = create_exercise(name="Sentadilla", type="gym")
    bench = create_exercise(name="Press banca", type="gym")
    create_strength_test_item(exercise_id=squat.id, weight_multiplier=1.5)
    create_strength_test_item(exercise_id=bench.id, weight_multiplier=1.0)
    create_bodyweight_log(athlete_id=member.id, weight_kg=80)
    base = datetime(2026, 5, 1, 8, 0, tzinfo=UTC)
    for i in range(2):
        create_strength_test_log(
            athlete_id=member.id,
            bodyweight_kg=80,
            performed_at=base + timedelta(days=i * 7),
            results={squat.id: 110 + i, bench.id: 78 + i},
        )
    log_in_as(member)

    page.goto(f"{app_url}/pruebas/fuerza")

    # A graph per exercise appears, with the current target shown (80×1.5 = 120 kg);
    # the internal multiplier is NOT shown anywhere.
    expect(page.get_by_role("heading", name="Resultados por ejercicio")).to_be_visible()
    expect(page.locator(".recharts-surface")).to_have_count(2)
    expect(page.get_by_text("Objetivo 120 kg").first).to_be_visible()
    expect(page.get_by_text("×1.5")).to_have_count(0)

    # The logs list is still there below.
    expect(page.get_by_role("heading", name="Tus registros")).to_be_visible()


def test_exercise_without_results_has_no_graph(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_bodyweight_log: Callable[..., BodyweightLog],
    create_strength_test_item: Callable[..., StrengthTestItem],
    create_strength_test_log: Callable[..., StrengthTestLog],
    log_in_as: Callable[[User], None],
) -> None:
    # Given two test exercises but results for only one.
    member = create_user(role="member", email="member@example.com")
    squat = create_exercise(name="Sentadilla", type="gym")
    create_exercise(name="Press banca", type="gym")  # in the test, but never performed
    create_strength_test_item(exercise_id=squat.id, weight_multiplier=1.5)
    create_bodyweight_log(athlete_id=member.id, weight_kg=80)
    create_strength_test_log(athlete_id=member.id, bodyweight_kg=80, results={squat.id: 110})
    log_in_as(member)

    page.goto(f"{app_url}/pruebas/fuerza")

    # Only the exercise with results gets a graph.
    expect(page.get_by_role("heading", name="Resultados por ejercicio")).to_be_visible()
    expect(page.locator(".recharts-surface")).to_have_count(1)


def test_no_graphs_section_without_any_results(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_strength_test_item: Callable[..., StrengthTestItem],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    squat = create_exercise(name="Sentadilla", type="gym")
    create_strength_test_item(exercise_id=squat.id, weight_multiplier=1.5)
    log_in_as(member)

    page.goto(f"{app_url}/pruebas/fuerza")
    expect(page.get_by_role("heading", name="Prueba de fuerza")).to_be_visible()
    expect(page.get_by_role("heading", name="Resultados por ejercicio")).to_have_count(0)
    expect(page.locator(".recharts-surface")).to_have_count(0)
