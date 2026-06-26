from collections.abc import Callable
from datetime import datetime, timedelta, timezone

from playwright.sync_api import Page, expect

from app.models import BodyweightLog, User

BASE = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


def test_add_bodyweight_shows_up_in_history(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)

    page.goto(f"{app_url}/registro-peso")
    expect(page.get_by_text("Todavía no has registrado tu peso.")).to_be_visible()

    page.get_by_label("Peso actual en kilos").fill("75.5")
    page.get_by_role("button", name="Guardar").click()
    expect(page.get_by_role("status").filter(has_text="Peso registrado.")).to_be_visible()

    # The new measurement appears in the history list.
    expect(page.get_by_text("75.5 kg")).to_be_visible()


def test_history_is_paginated_most_recent_first(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_bodyweight_log: Callable[..., BodyweightLog],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    # 12 logs → 2 pages of 10. weight_kg encodes the order: 100 is newest.
    for i in range(12):
        create_bodyweight_log(
            athlete_id=member.id,
            weight_kg=100 - i,
            recorded_at=BASE - timedelta(days=i),
        )
    log_in_as(member)

    page.goto(f"{app_url}/registro-peso")
    # Page 1: newest first → 100 kg at the top, 91 kg at the bottom (10 rows).
    expect(page.get_by_text("100 kg")).to_be_visible()
    expect(page.get_by_text("91 kg")).to_be_visible()
    expect(page.get_by_text("90 kg")).to_have_count(0)

    # Page 2 shows the two oldest (90, 89).
    page.get_by_role("button", name="2", exact=True).click()
    expect(page.get_by_text("90 kg")).to_be_visible()
    expect(page.get_by_text("89 kg")).to_be_visible()
    expect(page.get_by_text("100 kg")).to_have_count(0)


def test_graph_stays_fixed_while_paginating(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_bodyweight_log: Callable[..., BodyweightLog],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    for i in range(15):
        create_bodyweight_log(
            athlete_id=member.id,
            weight_kg=100 - i,
            recorded_at=BASE - timedelta(days=i),
        )
    log_in_as(member)

    page.goto(f"{app_url}/registro-peso")
    chart = page.locator(".recharts-wrapper")
    expect(chart).to_be_visible()
    # The chart plots exactly the last 10 points (one dot each).
    dots = page.locator(".recharts-line-dots circle")
    expect(dots).to_have_count(10)

    # Navigating the history list doesn't change the chart.
    page.get_by_role("button", name="2", exact=True).click()
    expect(page.get_by_text("86 kg")).to_be_visible()  # an older row now shown
    expect(dots).to_have_count(10)


def test_invalid_weight_is_rejected(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)

    page.goto(f"{app_url}/registro-peso")
    page.get_by_label("Peso actual en kilos").fill("-5")
    page.get_by_role("button", name="Guardar").click()
    expect(page.get_by_role("alert")).to_contain_text("peso válido")
    # Nothing was saved.
    expect(page.get_by_text("Todavía no has registrado tu peso.")).to_be_visible()
