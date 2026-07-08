from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from playwright.sync_api import Page, expect

from app.models import User


def test_test_result_graph_with_goal_band_relative_to_pb(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_lactic_acid_personal_best_log: Callable[..., object],
    create_lactic_acid_test_result_log: Callable[..., object],
    log_in_as: Callable[[User], None],
) -> None:
    # With a personal best of 40 s, the test-result goal band is pb+4.5 to pb+5 →
    # 44.5–45 s. The graph shows once there's at least one result.
    member = create_user(role="member", email="member@example.com")
    create_lactic_acid_personal_best_log(athlete_id=member.id, seconds=40.0)
    create_lactic_acid_test_result_log(athlete_id=member.id, seconds=46.0)
    log_in_as(member)

    page.goto(f"{app_url}/pruebas/acido-lactico")

    # The test-result tab is the default; its graph renders with the pb-relative band.
    expect(page.locator(".recharts-surface")).to_be_visible()
    expect(page.get_by_text("Objetivo 44.5–45 s")).to_be_visible()


def test_personal_best_graph_with_fixed_goal_band(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_lactic_acid_personal_best_log: Callable[..., object],
    log_in_as: Callable[[User], None],
) -> None:
    # The personal-best graph uses the fixed 26–27 s goal band. Seed several logs on
    # distinct days so the line has points.
    member = create_user(role="member", email="member@example.com")
    base = datetime(2026, 5, 1, 8, 0, tzinfo=UTC)
    for i in range(3):
        create_lactic_acid_personal_best_log(
            athlete_id=member.id,
            seconds=round(28.0 - i * 0.5, 1),
            performed_at=base + timedelta(days=i),
        )
    log_in_as(member)

    page.goto(f"{app_url}/pruebas/acido-lactico")
    page.get_by_role("tab", name="Marca personal").click()

    expect(page.locator(".recharts-surface")).to_be_visible()
    expect(page.get_by_text("Objetivo 26–27 s")).to_be_visible()
    # Three logs → three points on the line.
    expect(page.locator(".recharts-line-dots circle")).to_have_count(3)


def test_no_test_result_graph_without_logs(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_lactic_acid_personal_best_log: Callable[..., object],
    log_in_as: Callable[[User], None],
) -> None:
    # A personal best exists (so the table renders), but no test results yet → the
    # table shows without a graph.
    member = create_user(role="member", email="member@example.com")
    create_lactic_acid_personal_best_log(athlete_id=member.id, seconds=40.0)
    log_in_as(member)

    page.goto(f"{app_url}/pruebas/acido-lactico")
    expect(page.get_by_role("table")).to_be_visible()
    expect(page.locator(".recharts-surface")).to_have_count(0)


def test_no_personal_best_graph_without_logs(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # No logs at all: the personal-best tab shows the placeholder table, no graph.
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)

    page.goto(f"{app_url}/pruebas/acido-lactico")
    page.get_by_role("tab", name="Marca personal").click()
    expect(page.get_by_role("table")).to_be_visible()
    expect(page.locator(".recharts-surface")).to_have_count(0)
