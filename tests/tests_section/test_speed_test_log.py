from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import (
    Exercise,
    TrainingBlock,
    TrainingItem,
    TrainingItemKind,
    TrainingSession,
    TrainingSubBlock,
    User,
    Week,
    WeekRequirement,
)


def _speed_week(create_week: Callable[..., Week]) -> Week:
    return create_week(
        name="Semana prueba",
        phase="adaptation",
        requirements=[WeekRequirement(position=0, category="test", subtype="speed", count=1)],
    )


def _seed_warmup(create_exercise, create_training, create_speed_test_warmup) -> Exercise:
    """Make the warmup a pool session with one named exercise. Returns the exercise."""
    nado = create_exercise(name="Nado calentamiento", type="pool")
    warmup = create_training(
        title="Calentamiento",
        category="pool",
        subtype="endurance",
        position=-1,
        blocks=[
            TrainingBlock(
                name="Activación",
                position=0,
                sub_blocks=[
                    TrainingSubBlock(
                        name="Series",
                        position=0,
                        items=[
                            TrainingItem(
                                kind=TrainingItemKind.series,
                                position=0,
                                exercise_id=nado.id,
                                distance_meters=100,
                            )
                        ],
                    )
                ],
            )
        ],
    )
    create_speed_test_warmup(training_session_id=warmup.id)
    return nado


def test_register_shows_warmup_without_logging_controls(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    create_speed_test_warmup: Callable[..., object],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    _seed_warmup(create_exercise, create_training, create_speed_test_warmup)
    log_in_as(member)

    # Start the test from the explanation page.
    page.goto(f"{app_url}/pruebas/velocidad")
    page.get_by_role("link", name="Empezar prueba").click()
    expect(page).to_have_url(f"{app_url}/pruebas/velocidad/registrar")

    main = page.get_by_role("main")
    # The warmup is shown read-only (session-details style, exercise is a link).
    expect(main.get_by_role("heading", name="Activación")).to_be_visible()
    expect(main.get_by_role("button", name="Nado calentamiento")).to_be_visible()
    # No logging controls from the register-session flow (no "Hecho" buttons).
    expect(main.get_by_role("button", name="Hecho")).to_have_count(0)
    # The time input is present.
    expect(main.get_by_label("Tiempo en segundos")).to_be_visible()


def test_log_speed_test_counts_toward_week(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    create_speed_test_warmup: Callable[..., object],
    create_week: Callable[..., Week],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    _seed_warmup(create_exercise, create_training, create_speed_test_warmup)
    week = _speed_week(create_week)
    log_in_as(member)

    # Record a time (with decimals) and link it to the week.
    page.goto(f"{app_url}/pruebas/velocidad/registrar")
    page.get_by_label("Tiempo en segundos").fill("11.5")
    page.get_by_label("Semana", exact=True).select_option(label="Semana prueba")
    page.get_by_role("button", name="Finalizar prueba").click()
    expect(page.get_by_role("status").filter(has_text="Prueba registrada.")).to_be_visible()

    # It shows in the athlete's own log list, which links to the full log.
    expect(page).to_have_url(f"{app_url}/pruebas/velocidad")
    page.locator("a[href*='/pruebas/velocidad/registros/']").click()
    page.wait_for_url("**/pruebas/velocidad/registros/**")
    # "Tiempo: 11.5 s" is unique to the detail page (the scoring table also shows
    # bare times, so assert on the labelled value).
    expect(page.get_by_role("main").get_by_text("Tiempo:", exact=False)).to_contain_text("11.5 s")

    # The week counts the speed test as complete (1/1), linking back to the log.
    page.goto(f"{app_url}/calendario/{week.id}")
    expect(page.get_by_text("1/1", exact=True)).to_be_visible()
    log_link = page.locator("a[href*='/pruebas/velocidad/registros/']")
    expect(log_link).to_be_visible()
    log_link.click()
    page.wait_for_url("**/pruebas/velocidad/registros/**")
    expect(page.get_by_role("main").get_by_text("Tiempo:", exact=False)).to_contain_text("11.5 s")


def test_register_blocks_without_time(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    create_speed_test_warmup: Callable[..., object],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    _seed_warmup(create_exercise, create_training, create_speed_test_warmup)
    log_in_as(member)

    page.goto(f"{app_url}/pruebas/velocidad/registrar")
    page.get_by_role("button", name="Finalizar prueba").click()
    expect(page.get_by_role("alert")).to_contain_text("tiempo en segundos")
