from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import TrainingSession, User


def _drag_row_past(page: Page, source_index: int, target_index: int) -> None:
    """Drag the source training row's handle past the target row.

    dnd-kit's PointerSensor needs real PointerEvents (page.mouse dispatches plain
    MouseEvents it ignores), and pointerdown must fire on the handle node itself.
    """
    page.evaluate(
        """async ([fromIdx, toIdx]) => {
          const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
          const handles = document.querySelectorAll('[aria-label="Reordenar entrenamiento"]');
          const source = handles[fromIdx];
          const target = handles[toIdx];
          const sr = source.getBoundingClientRect();
          const tr = target.getBoundingClientRect();
          const cx = sr.x + sr.width / 2;
          const cy = sr.y + sr.height / 2;
          const dropY = tr.y + tr.height / 2 + (toIdx > fromIdx ? 10 : -10);
          const opts = (x, y) => ({
            bubbles: true, cancelable: true, composed: true,
            pointerId: 1, pointerType: 'mouse', isPrimary: true,
            button: 0, buttons: 1, clientX: x, clientY: y,
          });
          source.dispatchEvent(new PointerEvent('pointerdown', opts(cx, cy)));
          await sleep(60);
          document.dispatchEvent(new PointerEvent('pointermove', opts(cx, cy + (toIdx > fromIdx ? 20 : -20))));
          await sleep(80);
          document.dispatchEvent(new PointerEvent('pointermove', opts(cx, dropY)));
          await sleep(80);
          document.dispatchEvent(new PointerEvent('pointerup', opts(cx, dropY)));
        }""",
        [source_index, target_index],
    )
    page.wait_for_timeout(200)


def _titles_in_order(page: Page) -> list[str]:
    return page.get_by_role("listitem").all_inner_texts()


def test_admin_reorders_trainings_and_persists(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given three trainings in one subtype (seeded in order A, B, C).
    admin = create_user(role="admin", email="admin@example.com")
    for title in ("A", "B", "C"):
        create_training(title=title, category="gym", subtype="accumulation")
    log_in_as(admin)
    page.goto(f"{app_url}/entrenamientos/gimnasio/acumulacion")
    expect(page.get_by_role("listitem")).to_have_count(3)

    # When I drag the first row (A) below the third (C).
    _drag_row_past(page, source_index=0, target_index=2)

    # Then the optimistic order is B, C, A, and it persists after reload.
    expect(page.get_by_role("listitem")).to_have_text(["B", "C", "A"])
    page.reload()
    expect(page.get_by_role("listitem")).to_have_text(["B", "C", "A"])


def test_member_cannot_reorder(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given trainings and a logged-in member.
    member = create_user(role="member", email="member@example.com")
    for title in ("A", "B"):
        create_training(title=title, category="gym", subtype="accumulation")
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos/gimnasio/acumulacion")

    # Then there are no drag handles.
    expect(page.get_by_role("button", name="Reordenar entrenamiento")).to_have_count(0)


def test_no_reorder_while_searching(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an admin viewing a subtype list.
    admin = create_user(role="admin", email="admin@example.com")
    for title in ("Alpha", "Beta"):
        create_training(title=title, category="gym", subtype="accumulation")
    log_in_as(admin)
    page.goto(f"{app_url}/entrenamientos/gimnasio/acumulacion")

    # Handles are present unfiltered.
    expect(page.get_by_role("button", name="Reordenar entrenamiento")).to_have_count(2)

    # When I search, reordering is disabled (handles disappear).
    page.get_by_label("Buscar").fill("Alpha")
    expect(page.get_by_role("button", name="Reordenar entrenamiento")).to_have_count(0)
