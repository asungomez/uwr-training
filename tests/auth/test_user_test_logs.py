import re
from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import Exercise, SpeedTestLog, StrengthTestLog, User


def test_admin_sees_user_tests_across_types(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_strength_test_log: Callable[..., StrengthTestLog],
    create_speed_test_log: Callable[..., SpeedTestLog],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a member with one strength test and one speed test.
    admin = create_user(role="admin", email="admin@example.com")
    member = create_user(role="member", email="member@example.com")
    bench = create_exercise(name="Press banca")
    create_strength_test_log(athlete_id=member.id, bodyweight_kg=75, results={bench.id: 62.5})
    create_speed_test_log(athlete_id=member.id, seconds=11.5)
    log_in_as(admin)

    page.goto(f"{app_url}/usuarios/{member.id}")
    # Switching to the Pruebas tab updates the URL and lists both test types.
    page.get_by_role("button", name="Pruebas").click()
    expect(page).to_have_url(f"{app_url}/usuarios/{member.id}/pruebas")
    expect(page.get_by_text("75 kg de referencia", exact=False)).to_be_visible()
    expect(page.get_by_text("11.5 s", exact=False)).to_be_visible()


def test_type_filter_narrows_the_list(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_strength_test_log: Callable[..., StrengthTestLog],
    create_speed_test_log: Callable[..., SpeedTestLog],
    log_in_as: Callable[[User], None],
) -> None:
    admin = create_user(role="admin", email="admin@example.com")
    member = create_user(role="member", email="member@example.com")
    bench = create_exercise(name="Press banca")
    create_strength_test_log(athlete_id=member.id, bodyweight_kg=75, results={bench.id: 62.5})
    create_speed_test_log(athlete_id=member.id, seconds=11.5)
    log_in_as(admin)

    page.goto(f"{app_url}/usuarios/{member.id}/pruebas")
    expect(page.get_by_text("75 kg de referencia", exact=False)).to_be_visible()

    # Filtering to Velocidad leaves only the speed test.
    page.get_by_label("Filtrar por tipo").select_option("speed")
    expect(page.get_by_text("11.5 s", exact=False)).to_be_visible()
    expect(page.get_by_text("75 kg de referencia", exact=False)).to_have_count(0)


def test_clicking_a_test_opens_its_read_only_detail(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    create_strength_test_log: Callable[..., StrengthTestLog],
    create_speed_test_log: Callable[..., SpeedTestLog],
    log_in_as: Callable[[User], None],
) -> None:
    admin = create_user(role="admin", email="admin@example.com")
    member = create_user(role="member", email="member@example.com")
    bench = create_exercise(name="Press banca")
    create_strength_test_log(athlete_id=member.id, bodyweight_kg=75, results={bench.id: 62.5})
    create_speed_test_log(athlete_id=member.id, seconds=11.5)
    log_in_as(admin)

    page.goto(f"{app_url}/usuarios/{member.id}/pruebas")
    # Open the strength test (its exercise + lifted weight prove the detail loaded).
    strength_row = page.get_by_role("link").filter(has_text="75 kg de referencia")
    expect(strength_row).to_be_visible()
    strength_row.click()
    expect(page).to_have_url(re.compile(r"/pruebas/fuerza/"))
    expect(page.get_by_text("Press banca", exact=False)).to_be_visible()
    expect(page.get_by_text("62.5 kg", exact=False)).to_be_visible()


def test_member_cannot_access_user_test_logs(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    other = create_user(role="member", email="other@example.com")
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)

    # The whole /usuarios subtree is admin-only, including the tests tab.
    page.goto(f"{app_url}/usuarios/{other.id}/pruebas")
    expect(page).to_have_url(f"{app_url}/entrenamientos")
