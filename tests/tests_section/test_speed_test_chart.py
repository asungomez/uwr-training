from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from playwright.sync_api import Page, expect

from app.models import SpeedTestLog, User


def _seed_logs(
    create_speed_test_log: Callable[..., SpeedTestLog], athlete_id: object, count: int
) -> None:
    """`count` speed-test logs on distinct days (oldest first), descending times."""
    base = datetime(2026, 5, 1, 8, 0, tzinfo=UTC)
    for i in range(count):
        create_speed_test_log(
            athlete_id=athlete_id,
            seconds=round(14.0 - i * 0.2, 1),
            performed_at=base + timedelta(days=i),
        )


def test_chart_shows_with_one_log_and_goal_band(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_speed_test_log: Callable[..., SpeedTestLog],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a single speed-test log.
    member = create_user(role="member", email="member@example.com")
    _seed_logs(create_speed_test_log, member.id, 1)
    log_in_as(member)

    page.goto(f"{app_url}/pruebas/velocidad")

    # The chart renders (with its goal band) as soon as there's one log.
    expect(page.get_by_role("heading", name="Tus registros")).to_be_visible()
    expect(page.locator(".recharts-surface")).to_be_visible()
    expect(page.get_by_text("Objetivo 12.5–13 s")).to_be_visible()


def test_chart_plots_last_ten_regardless_of_page(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_speed_test_log: Callable[..., SpeedTestLog],
    log_in_as: Callable[[User], None],
) -> None:
    # Given 12 logs — more than one list page (PAGE_SIZE 10) and more than the
    # graph's 10 points.
    member = create_user(role="member", email="member@example.com")
    _seed_logs(create_speed_test_log, member.id, 12)
    log_in_as(member)

    page.goto(f"{app_url}/pruebas/velocidad")
    dots = page.locator(".recharts-line-dots circle")
    expect(dots).to_have_count(10)  # last 10 of the 12

    # Moving to list page 2 doesn't change the chart — it always shows the last 10.
    page.get_by_role("button", name="Página siguiente").click()
    expect(page.get_by_role("link", name="s", exact=False).first).to_be_visible()
    expect(dots).to_have_count(10)
    expect(page.get_by_text("Objetivo 12.5–13 s")).to_be_visible()


def test_no_chart_without_logs(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)

    page.goto(f"{app_url}/pruebas/velocidad")
    expect(page.get_by_text("Todavía no has hecho ninguna prueba.")).to_be_visible()
    expect(page.locator(".recharts-surface")).to_have_count(0)
