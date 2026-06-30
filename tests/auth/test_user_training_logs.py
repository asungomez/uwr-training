import re
from collections.abc import Callable

import sqlalchemy
from playwright.sync_api import Page, expect
from sqlalchemy.orm import Session

from app.models import CardioSessionLog, CardioTraining, SessionLog, TrainingSession, User


def _seed_logs(
    engine: sqlalchemy.Engine,
    *,
    athlete_id: object,
    gym_id: object,
    pool_id: object,
    cardio_id: object,
) -> None:
    """One log of each kind for the athlete (performed_at defaults to now)."""
    with Session(engine, expire_on_commit=False) as session:
        session.add_all(
            [
                SessionLog(
                    training_session_id=gym_id,
                    athlete_id=athlete_id,
                    note="Sesión de fuerza",
                ),
                SessionLog(training_session_id=pool_id, athlete_id=athlete_id),
                CardioSessionLog(
                    cardio_training_id=cardio_id, athlete_id=athlete_id, exercise="running"
                ),
            ]
        )
        session.commit()


def test_admin_sees_user_logs_across_categories(
    page: Page,
    app_url: str,
    _db_engine: sqlalchemy.Engine,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    create_cardio_training: Callable[..., CardioTraining],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a member with one gym, one pool and one cardio log.
    admin = create_user(role="admin", email="admin@example.com")
    member = create_user(role="member", email="member@example.com")
    gym = create_training(title="Fuerza A", category="gym", subtype="accumulation")
    pool = create_training(title="Piscina B", category="pool", subtype="endurance")
    cardio = create_cardio_training(title="Carrera C", subtype="aerobic")
    _seed_logs(
        _db_engine, athlete_id=member.id, gym_id=gym.id, pool_id=pool.id, cardio_id=cardio.id
    )
    log_in_as(admin)

    # The detail opens on the Información tab.
    page.goto(f"{app_url}/usuarios/{member.id}")
    expect(page.get_by_role("definition").filter(has_text="member@example.com")).to_be_visible()

    # Switching to Entrenamientos updates the URL and lists all three categories.
    page.get_by_role("button", name="Entrenamientos").click()
    expect(page).to_have_url(f"{app_url}/usuarios/{member.id}/entrenamientos")
    expect(page.get_by_text("Fuerza A", exact=False)).to_be_visible()
    expect(page.get_by_text("Piscina B", exact=False)).to_be_visible()
    expect(page.get_by_text("Carrera C", exact=False)).to_be_visible()


def test_category_filter_narrows_the_list(
    page: Page,
    app_url: str,
    _db_engine: sqlalchemy.Engine,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    create_cardio_training: Callable[..., CardioTraining],
    log_in_as: Callable[[User], None],
) -> None:
    admin = create_user(role="admin", email="admin@example.com")
    member = create_user(role="member", email="member@example.com")
    gym = create_training(title="Fuerza A", category="gym", subtype="accumulation")
    pool = create_training(title="Piscina B", category="pool", subtype="endurance")
    cardio = create_cardio_training(title="Carrera C", subtype="aerobic")
    _seed_logs(
        _db_engine, athlete_id=member.id, gym_id=gym.id, pool_id=pool.id, cardio_id=cardio.id
    )
    log_in_as(admin)

    page.goto(f"{app_url}/usuarios/{member.id}/entrenamientos")
    expect(page.get_by_text("Fuerza A", exact=False)).to_be_visible()

    # Filtering to Cardio leaves only the cardio log.
    page.get_by_label("Filtrar por categoría").select_option("cardio")
    expect(page.get_by_text("Carrera C", exact=False)).to_be_visible()
    expect(page.get_by_text("Fuerza A", exact=False)).to_have_count(0)
    expect(page.get_by_text("Piscina B", exact=False)).to_have_count(0)


def test_clicking_a_log_opens_its_read_only_detail(
    page: Page,
    app_url: str,
    _db_engine: sqlalchemy.Engine,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    create_cardio_training: Callable[..., CardioTraining],
    log_in_as: Callable[[User], None],
) -> None:
    admin = create_user(role="admin", email="admin@example.com")
    member = create_user(role="member", email="member@example.com")
    gym = create_training(title="Fuerza A", category="gym", subtype="accumulation")
    pool = create_training(title="Piscina B", category="pool", subtype="endurance")
    cardio = create_cardio_training(title="Carrera C", subtype="aerobic")
    _seed_logs(
        _db_engine, athlete_id=member.id, gym_id=gym.id, pool_id=pool.id, cardio_id=cardio.id
    )
    log_in_as(admin)

    page.goto(f"{app_url}/usuarios/{member.id}/entrenamientos")
    # Open the gym log (its note proves the detail loaded, not just the title).
    page.get_by_role("link").filter(has_text="Gimnasio").click()
    expect(page).to_have_url(re.compile(r"/registros/sesion/"))
    expect(page.get_by_text("Fuerza A", exact=False)).to_be_visible()
    expect(page.get_by_text("Sesión de fuerza", exact=False)).to_be_visible()


def test_member_cannot_access_user_training_logs(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    other = create_user(role="member", email="other@example.com")
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)

    # The whole /usuarios subtree is admin-only, including the logs tab.
    page.goto(f"{app_url}/usuarios/{other.id}/entrenamientos")
    expect(page).to_have_url(f"{app_url}/entrenamientos")
