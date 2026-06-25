from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import (
    Exercise,
    TrainingBlock,
    TrainingCategory,
    TrainingItem,
    TrainingItemKind,
    TrainingSession,
    TrainingSubBlock,
    TrainingSubtype,
    User,
    Week,
    WeekRequirement,
)


def _gym_training(
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
) -> TrainingSession:
    squat = create_exercise(name="Sentadilla", type="gym")
    return create_training(
        title="Fuerza máxima",
        category="gym",
        subtype="accumulation",
        blocks=[
            TrainingBlock(
                name="Bloque",
                position=0,
                sub_blocks=[
                    TrainingSubBlock(
                        name="Sub",
                        position=0,
                        items=[
                            TrainingItem(
                                kind=TrainingItemKind.series, position=0, exercise_id=squat.id
                            )
                        ],
                    )
                ],
            )
        ],
    )


def _week(create_week: Callable[..., Week]) -> Week:
    return create_week(
        name="Semana Prog",
        phase="accumulation",
        requirements=[
            WeekRequirement(
                position=0,
                category=TrainingCategory.gym,
                subtype=TrainingSubtype.accumulation,
                count=2,
            )
        ],
    )


def _register_linked(page: Page, app_url: str, training_id: str) -> None:
    """Log the session, marking the exercise done and linking it to 'Semana Prog'."""
    page.goto(f"{app_url}/entrenamientos/{training_id}/registrar")
    page.get_by_role("button", name="Hecho").first.click()
    page.get_by_label("Semana", exact=True).select_option(label="Semana Prog")
    page.get_by_role("button", name="Finalizar sesión").click()
    expect(page.get_by_role("status").filter(has_text="Sesión registrada.")).to_be_visible()


def test_list_shows_progress(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    create_week: Callable[..., Week],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    training = _gym_training(create_exercise, create_training)
    _week(create_week)
    log_in_as(member)

    # No logs yet → 0/2.
    page.goto(f"{app_url}/calendario")
    row = page.get_by_role("listitem").filter(has_text="Semana Prog")
    expect(row.get_by_text("Gimnasio · Acumulación", exact=False)).to_contain_text("0/2")

    # Log one → 1/2.
    _register_linked(page, app_url, str(training.id))
    page.goto(f"{app_url}/calendario")
    row = page.get_by_role("listitem").filter(has_text="Semana Prog")
    expect(row.get_by_text("Gimnasio · Acumulación", exact=False)).to_contain_text("1/2")


def test_detail_shows_progress_logs_and_category_link(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    create_week: Callable[..., Week],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    training = _gym_training(create_exercise, create_training)
    week = _week(create_week)
    log_in_as(member)
    _register_linked(page, app_url, str(training.id))

    page.goto(f"{app_url}/calendario/{week.id}")
    main = page.get_by_role("main")

    # Progress + the logged training under the requirement.
    expect(main.get_by_text("1/2")).to_be_visible()
    expect(main.get_by_text("Fuerza máxima")).to_be_visible()

    # The category links to its trainings list.
    expect(main.get_by_role("link", name="Gimnasio · Acumulación")).to_have_attribute(
        "href", "/entrenamientos/gimnasio/acumulacion"
    )

    # The logged training links to its log detail.
    main.get_by_role("link", name="Fuerza máxima").click()
    page.wait_for_url("**/registros/**")


def test_progress_is_per_athlete(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    create_week: Callable[..., Week],
    log_in_as: Callable[[User], None],
) -> None:
    # One athlete logs a session linked to the week.
    author = create_user(role="member", email="author@example.com")
    training = _gym_training(create_exercise, create_training)
    week = _week(create_week)
    log_in_as(author)
    _register_linked(page, app_url, str(training.id))

    # A different athlete sees 0/2 (the log isn't theirs).
    other = create_user(role="member", email="other@example.com")
    log_in_as(other)
    page.goto(f"{app_url}/calendario/{week.id}")
    main = page.get_by_role("main")
    expect(main.get_by_text("0/2")).to_be_visible()
    expect(main.get_by_text("Fuerza máxima")).to_have_count(0)
