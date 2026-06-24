from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import (
    TrainingBlock,
    TrainingItem,
    TrainingItemKind,
    TrainingSession,
    TrainingSubBlock,
    User,
)


def _go_to_new_form(page: Page, app_url: str) -> None:
    page.goto(f"{app_url}/entrenamientos/nuevo")
    page.get_by_label("Título").fill("Sesión con notas")
    page.get_by_label("Categoría").select_option(label="Gimnasio")
    page.get_by_label("Subtipo").select_option(label="Acumulación")
    page.get_by_role("button", name="Añadir bloque").click()
    page.get_by_label("Nombre del bloque").fill("Bloque")
    page.get_by_role("button", name="Añadir sub-bloque").click()
    page.get_by_label("Nombre del sub-bloque").fill("Sub")


def _note(text: str, position: int) -> TrainingItem:
    return TrainingItem(kind=TrainingItemKind.note, text=text, position=position)


def _drag_handle_past(page: Page, handle_label: str, source_index: int, target_index: int) -> None:
    """Reorder by dragging the `source_index`-th `handle_label` handle past the
    `target_index`-th one (both selected by aria-label).

    dnd-kit's PointerSensor listens for real PointerEvents (pointerId / pointerType);
    Playwright's page.mouse.* dispatches plain MouseEvents the sensor ignores, so the
    drag never starts. We dispatch PointerEvents instead — and fire `pointerdown` on
    the handle element itself (a coordinate hit-test lands on the wrong node and the
    sensor never binds). Moves go on `document` with pauses for dnd-kit's rAF-based
    handling; coordinates are read in-page so mid-drag layout shifts don't matter.
    """
    page.evaluate(
        """async ([label, fromIdx, toIdx]) => {
          const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
          const handles = document.querySelectorAll(`[aria-label="${label}"]`);
          const source = handles[fromIdx];
          const target = handles[toIdx];
          const sr = source.getBoundingClientRect();
          const tr = target.getBoundingClientRect();
          const cx = sr.x + sr.width / 2;
          const cy = sr.y + sr.height / 2;
          // Past the target handle's centre (offset toward the drag direction) so
          // closestCenter resolves to the target slot.
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
        [handle_label, source_index, target_index],
    )
    page.wait_for_timeout(150)


# ---------------------------------------------------------------- happy paths


def test_admin_adds_notes_when_creating(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a new training with a block + sub-block.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    _go_to_new_form(page, app_url)

    # When I add two notes and save.
    page.get_by_role("button", name="Añadir nota").click()
    page.get_by_role("button", name="Añadir nota").click()
    notes = page.get_by_label("Nota", exact=True)
    notes.nth(0).fill("10s de descanso")
    notes.nth(1).fill("quítate las aletas")
    page.get_by_role("button", name="Crear entrenamiento").click()

    # Then the detail page shows both notes.
    expect(page.get_by_role("status").filter(has_text="Entrenamiento creado.")).to_be_visible()
    expect(page.get_by_text("10s de descanso")).to_be_visible()
    expect(page.get_by_text("quítate las aletas")).to_be_visible()


def test_edit_prefills_notes_and_persists_changes(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a sub-block with two notes.
    admin = create_user(role="admin", email="admin@example.com")
    training = create_training(
        title="Editable",
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
                        items=[_note("Primera", 0), _note("Segunda", 1)],
                    )
                ],
            )
        ],
    )
    log_in_as(admin)
    page.goto(f"{app_url}/entrenamientos/{training.id}/editar")

    # The existing notes are pre-filled.
    notes = page.get_by_label("Nota", exact=True)
    expect(notes).to_have_count(2)
    expect(notes.nth(0)).to_have_value("Primera")
    expect(notes.nth(1)).to_have_value("Segunda")

    # When I edit one, remove the other, and save.
    notes.nth(0).fill("Editada")
    page.get_by_role("button", name="Eliminar nota").nth(1).click()
    page.get_by_role("button", name="Guardar cambios").click()
    expect(page.get_by_role("status").filter(has_text="Entrenamiento actualizado.")).to_be_visible()

    # Then the change round-trips after reload.
    page.goto(f"{app_url}/entrenamientos/{training.id}/editar")
    edited = page.get_by_label("Nota", exact=True)
    expect(edited).to_have_count(1)
    expect(edited.nth(0)).to_have_value("Editada")


def test_reorder_notes_within_sub_block_persists(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a sub-block with two ordered notes.
    admin = create_user(role="admin", email="admin@example.com")
    training = create_training(
        title="Reordenable",
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
                        items=[_note("Primera", 0), _note("Segunda", 1)],
                    )
                ],
            )
        ],
    )
    log_in_as(admin)
    page.goto(f"{app_url}/entrenamientos/{training.id}/editar")

    # When I drag the first note below the second.
    notes = page.get_by_label("Nota", exact=True)
    expect(page.get_by_role("button", name="Reordenar nota")).to_have_count(2)
    _drag_handle_past(page, "Reordenar nota", source_index=0, target_index=1)

    # The order updates in place, then persists after save + reload.
    expect(notes.nth(0)).to_have_value("Segunda")
    expect(notes.nth(1)).to_have_value("Primera")

    page.get_by_role("button", name="Guardar cambios").click()
    expect(page.get_by_role("status").filter(has_text="Entrenamiento actualizado.")).to_be_visible()

    page.goto(f"{app_url}/entrenamientos/{training.id}/editar")
    reloaded = page.get_by_label("Nota", exact=True)
    expect(reloaded.nth(0)).to_have_value("Segunda")
    expect(reloaded.nth(1)).to_have_value("Primera")


def test_note_drag_stays_within_its_sub_block(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given two sub-blocks, each with one note.
    admin = create_user(role="admin", email="admin@example.com")
    training = create_training(
        title="Aislado",
        category="gym",
        subtype="accumulation",
        blocks=[
            TrainingBlock(
                name="Bloque",
                position=0,
                sub_blocks=[
                    TrainingSubBlock(name="Sub A", position=0, items=[_note("Nota A", 0)]),
                    TrainingSubBlock(name="Sub B", position=1, items=[_note("Nota B", 0)]),
                ],
            )
        ],
    )
    log_in_as(admin)
    page.goto(f"{app_url}/entrenamientos/{training.id}/editar")

    # When I try to drag Sub A's note onto Sub B's note, the nested DnD contexts
    # keep it isolated — nothing moves across sub-blocks.
    expect(page.get_by_role("button", name="Reordenar nota")).to_have_count(2)
    _drag_handle_past(page, "Reordenar nota", source_index=0, target_index=1)
    page.get_by_role("button", name="Guardar cambios").click()
    expect(page.get_by_role("status").filter(has_text="Entrenamiento actualizado.")).to_be_visible()

    # Then each sub-block still has exactly its own note after reload.
    page.goto(f"{app_url}/entrenamientos/{training.id}/editar")
    notes = page.get_by_label("Nota", exact=True)
    expect(notes).to_have_count(2)
    expect(notes.nth(0)).to_have_value("Nota A")
    expect(notes.nth(1)).to_have_value("Nota B")


def test_detail_shows_notes_in_order(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a sub-block with three ordered notes.
    member = create_user(role="member", email="member@example.com")
    training = create_training(
        title="Con notas",
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
                        items=[_note("Uno", 0), _note("Dos", 1), _note("Tres", 2)],
                    )
                ],
            )
        ],
    )
    log_in_as(member)

    # When I open the detail page, the notes render as an ordered list, in order.
    page.goto(f"{app_url}/entrenamientos/{training.id}")
    note_items = page.locator("ol li")
    expect(note_items).to_have_count(3)
    expect(note_items.nth(0)).to_have_text("Uno")
    expect(note_items.nth(1)).to_have_text("Dos")
    expect(note_items.nth(2)).to_have_text("Tres")


# ------------------------------------------------------------ not-so-happy path


def test_removing_note_returns_to_no_notes(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a sub-block with one added note.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    _go_to_new_form(page, app_url)
    page.get_by_role("button", name="Añadir nota").click()
    expect(page.get_by_label("Nota", exact=True)).to_have_count(1)

    # When I remove it, no note inputs remain.
    page.get_by_role("button", name="Eliminar nota").click()
    expect(page.get_by_label("Nota", exact=True)).to_have_count(0)
