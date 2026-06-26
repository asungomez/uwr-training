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


def _gym_accumulation_training(
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
) -> TrainingSession:
    squat = create_exercise(name="Sentadilla", type="gym")
    return create_training(
        title="Fuerza",
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


def _week(
    create_week: Callable[..., Week], name: str, category: str, subtype: str, count: int = 2
) -> Week:
    return create_week(
        name=name,
        phase="accumulation",
        requirements=[
            WeekRequirement(position=0, category=category, subtype=subtype, count=count)
        ],
    )


def test_register_offers_only_matching_weeks(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    create_week: Callable[..., Week],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    training = _gym_accumulation_training(create_exercise, create_training)
    _week(create_week, "Semana gym", "gym", "accumulation")
    _week(create_week, "Semana pool", "pool", "endurance")
    log_in_as(member)

    page.goto(f"{app_url}/entrenamientos/{training.id}/registrar")
    weeks = page.get_by_label("Semana", exact=True)
    expect(weeks.get_by_role("option", name="Semana gym")).to_be_attached()
    # The pool week doesn't recommend this gym/accumulation training.
    expect(weeks.get_by_role("option", name="Semana pool")).to_have_count(0)


def test_register_links_week_and_detail_can_change_it(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    create_week: Callable[..., Week],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    training = _gym_accumulation_training(create_exercise, create_training)
    _week(create_week, "Semana uno", "gym", "accumulation")
    _week(create_week, "Semana dos", "gym", "accumulation")
    log_in_as(member)

    # Register, choosing "Semana uno", with a note to find the log row by.
    page.goto(f"{app_url}/entrenamientos/{training.id}/registrar")
    page.get_by_role("button", name="Hecho").first.click()
    page.get_by_label("Semana", exact=True).select_option(label="Semana uno")
    page.get_by_label("Nota de la sesión", exact=False).fill("con semana")
    page.get_by_role("button", name="Finalizar sesión").click()
    expect(page.get_by_role("status").filter(has_text="Sesión registrada.")).to_be_visible()

    # Open the log from the detail page; its week is pre-selected.
    page.get_by_role("link", name="con semana").click()
    page.wait_for_url("**/registros/**")
    week = page.get_by_label("Semana", exact=True)
    expect(week).to_contain_text("Semana uno")  # the selected option's label

    # Change it to "Semana dos" → confirmation toast.
    week.select_option(label="Semana dos")
    expect(page.get_by_role("status").filter(has_text="Semana actualizada.")).to_be_visible()


def test_completed_week_drops_from_register_but_stays_on_edit(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_training: Callable[..., TrainingSession],
    create_week: Callable[..., Week],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    training = _gym_accumulation_training(create_exercise, create_training)
    # A week that only needs 1 of this type — one log fills it.
    _week(create_week, "Semana llena", "gym", "accumulation", count=1)
    log_in_as(member)

    # Log it, linking to "Semana llena" → that week is now complete (1/1).
    page.goto(f"{app_url}/entrenamientos/{training.id}/registrar")
    page.get_by_role("button", name="Hecho").first.click()
    page.get_by_label("Semana", exact=True).select_option(label="Semana llena")
    page.get_by_label("Nota de la sesión", exact=False).fill("llena")
    page.get_by_role("button", name="Finalizar sesión").click()
    expect(page.get_by_role("status").filter(has_text="Sesión registrada.")).to_be_visible()

    # Registering again no longer offers the full week (no week select at all here,
    # since it was the only recommending week).
    page.goto(f"{app_url}/entrenamientos/{training.id}/registrar")
    expect(page.get_by_label("Semana", exact=True)).to_have_count(0)

    # But the existing log keeps it selectable, so the link can still be edited.
    page.goto(f"{app_url}/entrenamientos/{training.id}")
    page.get_by_role("link", name="llena").click()
    page.wait_for_url("**/registros/**")
    week = page.get_by_label("Semana", exact=True)
    expect(week).to_contain_text("Semana llena")
