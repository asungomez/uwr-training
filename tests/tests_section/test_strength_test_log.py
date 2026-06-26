from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import (
    BodyweightLog,
    Exercise,
    StrengthTestItem,
    User,
    Week,
    WeekRequirement,
)


def _test_week(create_week: Callable[..., Week]) -> Week:
    return create_week(
        name="Semana prueba",
        phase="adaptation",
        requirements=[
            WeekRequirement(position=0, category="test", subtype="strength", count=1)
        ],
    )


def test_register_warns_when_no_bodyweight(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)

    page.goto(f"{app_url}/pruebas/fuerza/registrar")
    main = page.get_by_role("main")
    expect(main.get_by_text("al menos un registro de peso", exact=False)).to_be_visible()
    expect(main.get_by_role("link", name="Registrar peso")).to_be_visible()


def test_register_shows_targets_from_bodyweight(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_bodyweight_log: Callable[..., BodyweightLog],
    create_strength_test_item: Callable[..., StrengthTestItem],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    squat = create_exercise(name="Sentadilla", type="gym")
    create_strength_test_item(exercise_id=squat.id, weight_multiplier=1.5)
    create_bodyweight_log(athlete_id=member.id, weight_kg=80)
    log_in_as(member)

    page.goto(f"{app_url}/pruebas/fuerza/registrar")
    main = page.get_by_role("main")
    expect(main.get_by_text("80 kg", exact=False)).to_be_visible()
    expect(main.get_by_text("Sentadilla")).to_be_visible()
    # Target = 80 × 1.5 = 120.
    expect(main.get_by_text("Objetivo: 120 kg", exact=False)).to_be_visible()


def test_log_strength_test_counts_toward_week(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_bodyweight_log: Callable[..., BodyweightLog],
    create_strength_test_item: Callable[..., StrengthTestItem],
    create_week: Callable[..., Week],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    squat = create_exercise(name="Sentadilla", type="gym")
    create_strength_test_item(exercise_id=squat.id, weight_multiplier=1.5)
    create_bodyweight_log(athlete_id=member.id, weight_kg=80)
    week = _test_week(create_week)
    log_in_as(member)

    # Take the test: enter the lifted weight and link it to the week.
    page.goto(f"{app_url}/pruebas/fuerza/registrar")
    page.get_by_label("Peso levantado en Sentadilla").fill("110")
    page.get_by_label("Semana", exact=True).select_option(label="Semana prueba")
    page.get_by_role("button", name="Finalizar prueba").click()
    expect(page.get_by_role("status").filter(has_text="Prueba registrada.")).to_be_visible()

    # It shows in the athlete's own log list.
    expect(page).to_have_url(f"{app_url}/pruebas/fuerza")
    page.get_by_role("link", name="Peso corporal: 80 kg", exact=False).click()
    page.wait_for_url("**/pruebas/fuerza/registros/**")
    main = page.get_by_role("main")
    expect(main.get_by_text("110 kg", exact=False)).to_be_visible()
    expect(main.get_by_text("objetivo 120 kg", exact=False)).to_be_visible()

    # The week now counts the test as complete (1/1), linking back to the log.
    page.goto(f"{app_url}/calendario/{week.id}")
    expect(page.get_by_text("1/1", exact=True)).to_be_visible()
    log_link = page.locator("a[href*='/pruebas/fuerza/registros/']")
    expect(log_link).to_be_visible()
    log_link.click()
    page.wait_for_url("**/pruebas/fuerza/registros/**")
    expect(page.get_by_role("main").get_by_text("110 kg", exact=False)).to_be_visible()


def test_register_blocks_without_all_weights(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_bodyweight_log: Callable[..., BodyweightLog],
    create_strength_test_item: Callable[..., StrengthTestItem],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    squat = create_exercise(name="Sentadilla", type="gym")
    bench = create_exercise(name="Press banca", type="gym")
    create_strength_test_item(exercise_id=squat.id, weight_multiplier=1.5)
    create_strength_test_item(exercise_id=bench.id, weight_multiplier=1.0)
    create_bodyweight_log(athlete_id=member.id, weight_kg=80)
    log_in_as(member)

    page.goto(f"{app_url}/pruebas/fuerza/registrar")
    # Fill only one of the two → submit is blocked with a message.
    page.get_by_label("Peso levantado en Sentadilla").fill("100")
    page.get_by_role("button", name="Finalizar prueba").click()
    expect(page.get_by_role("alert")).to_contain_text("peso levantado")
