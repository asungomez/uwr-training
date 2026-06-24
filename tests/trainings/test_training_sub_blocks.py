from collections.abc import Callable

from playwright.sync_api import Locator, Page, expect

from app.models import TrainingBlock, TrainingSession, TrainingSubBlock, User


def _go_to_new_form(page: Page, app_url: str) -> None:
    page.goto(f"{app_url}/entrenamientos/nuevo")
    page.get_by_label("Título").fill("Sesión anidada")
    page.get_by_label("Categoría").select_option(label="Gimnasio")
    page.get_by_label("Subtipo").select_option(label="Acumulación")


def _drag_below(page: Page, source: Locator, target: Locator) -> None:
    """Drag the source handle past the target handle (dnd-kit pointer drag)."""
    sbox = source.bounding_box()
    tbox = target.bounding_box()
    assert sbox is not None and tbox is not None
    page.mouse.move(sbox["x"] + sbox["width"] / 2, sbox["y"] + sbox["height"] / 2)
    page.mouse.down()
    page.mouse.move(sbox["x"] + 5, sbox["y"] + 15)
    page.mouse.move(tbox["x"] + tbox["width"] / 2, tbox["y"] + tbox["height"] + 10, steps=10)
    page.mouse.up()


# ---------------------------------------------------------------- happy paths


def test_admin_creates_training_with_sub_blocks(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given the new-training form with a block.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    _go_to_new_form(page, app_url)
    page.get_by_role("button", name="Añadir bloque").click()
    page.get_by_label("Nombre del bloque").fill("Tren superior")

    # When I add a sub-block with a name and notes, then save.
    page.get_by_role("button", name="Añadir sub-bloque").click()
    page.get_by_label("Nombre del sub-bloque").fill("Preparación")
    page.get_by_label("Notas del sub-bloque").fill("Repetir 2 veces")
    page.get_by_role("button", name="Crear entrenamiento").click()

    # Then it's created and the detail page shows the block with its sub-block.
    expect(page.get_by_role("status").filter(has_text="Entrenamiento creado.")).to_be_visible()
    expect(page.get_by_role("heading", name="Tren superior")).to_be_visible()
    expect(page.get_by_role("heading", name="Preparación")).to_be_visible()
    expect(page.get_by_text("Repetir 2 veces")).to_be_visible()


def test_empty_block_shows_no_sub_block_state(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a freshly added block.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    _go_to_new_form(page, app_url)
    page.get_by_role("button", name="Añadir bloque").click()

    # Then it shows the empty sub-block state until one is added.
    expect(page.get_by_text("Todavía no hay sub-bloques.")).to_be_visible()
    page.get_by_role("button", name="Añadir sub-bloque").click()
    expect(page.get_by_label("Nombre del sub-bloque")).to_have_count(1)
    expect(page.get_by_text("Todavía no hay sub-bloques.")).not_to_be_visible()


def test_edit_prefills_sub_blocks_and_persists_changes(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a training whose block has two sub-blocks.
    admin = create_user(role="admin", email="admin@example.com")
    training = create_training(
        title="Editable",
        category="gym",
        subtype="accumulation",
        blocks=[
            TrainingBlock(
                name="Tren superior",
                position=0,
                sub_blocks=[
                    TrainingSubBlock(name="Preparación", notes="Suave", position=0),
                    TrainingSubBlock(name="Principal", notes=None, position=1),
                ],
            )
        ],
    )
    log_in_as(admin)
    page.goto(f"{app_url}/entrenamientos/{training.id}/editar")

    # The existing sub-blocks are pre-filled.
    names = page.get_by_label("Nombre del sub-bloque")
    expect(names).to_have_count(2)
    expect(names.nth(0)).to_have_value("Preparación")
    expect(names.nth(1)).to_have_value("Principal")
    expect(page.get_by_label("Notas del sub-bloque").nth(0)).to_have_value("Suave")

    # When I rename the first, remove the second, and save.
    names.nth(0).fill("Activación")
    page.get_by_role("button", name="Eliminar sub-bloque").nth(1).click()
    page.get_by_role("button", name="Guardar cambios").click()
    expect(page.get_by_role("status").filter(has_text="Entrenamiento actualizado.")).to_be_visible()

    # Then the change round-trips after reload.
    page.goto(f"{app_url}/entrenamientos/{training.id}/editar")
    edited = page.get_by_label("Nombre del sub-bloque")
    expect(edited).to_have_count(1)
    expect(edited.nth(0)).to_have_value("Activación")


def test_reorder_sub_blocks_within_block_persists(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a block with two ordered sub-blocks.
    admin = create_user(role="admin", email="admin@example.com")
    training = create_training(
        title="Reordenable",
        category="gym",
        subtype="accumulation",
        blocks=[
            TrainingBlock(
                name="Tren superior",
                position=0,
                sub_blocks=[
                    TrainingSubBlock(name="Primero", position=0),
                    TrainingSubBlock(name="Segundo", position=1),
                ],
            )
        ],
    )
    log_in_as(admin)
    page.goto(f"{app_url}/entrenamientos/{training.id}/editar")

    # When I drag the first sub-block below the second.
    handles = page.get_by_role("button", name="Reordenar sub-bloque")
    expect(handles).to_have_count(2)
    _drag_below(page, handles.nth(0), handles.nth(1))

    # The order updates in place, then persists after save + reload.
    names = page.get_by_label("Nombre del sub-bloque")
    expect(names.nth(0)).to_have_value("Segundo")
    expect(names.nth(1)).to_have_value("Primero")

    page.get_by_role("button", name="Guardar cambios").click()
    expect(page.get_by_role("status").filter(has_text="Entrenamiento actualizado.")).to_be_visible()

    page.goto(f"{app_url}/entrenamientos/{training.id}/editar")
    reloaded = page.get_by_label("Nombre del sub-bloque")
    expect(reloaded.nth(0)).to_have_value("Segundo")
    expect(reloaded.nth(1)).to_have_value("Primero")


def test_sub_block_drag_stays_within_its_block(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given two blocks, each with one sub-block.
    admin = create_user(role="admin", email="admin@example.com")
    training = create_training(
        title="Aislado",
        category="gym",
        subtype="accumulation",
        blocks=[
            TrainingBlock(
                name="Bloque A",
                position=0,
                sub_blocks=[TrainingSubBlock(name="Sub A", position=0)],
            ),
            TrainingBlock(
                name="Bloque B",
                position=1,
                sub_blocks=[TrainingSubBlock(name="Sub B", position=0)],
            ),
        ],
    )
    log_in_as(admin)
    page.goto(f"{app_url}/entrenamientos/{training.id}/editar")

    # When I try to drag Block A's sub-block onto Block B's sub-block, the nested
    # DnD contexts keep it isolated — nothing moves across blocks.
    handles = page.get_by_role("button", name="Reordenar sub-bloque")
    expect(handles).to_have_count(2)
    _drag_below(page, handles.nth(0), handles.nth(1))
    page.get_by_role("button", name="Guardar cambios").click()
    expect(page.get_by_role("status").filter(has_text="Entrenamiento actualizado.")).to_be_visible()

    # Then each block still has exactly its own single sub-block after reload.
    page.goto(f"{app_url}/entrenamientos/{training.id}/editar")
    names = page.get_by_label("Nombre del sub-bloque")
    expect(names).to_have_count(2)
    expect(names.nth(0)).to_have_value("Sub A")
    expect(names.nth(1)).to_have_value("Sub B")


# ------------------------------------------------------------ not-so-happy paths


def test_blank_sub_block_name_blocks_save(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a named block with an empty sub-block.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    _go_to_new_form(page, app_url)
    page.get_by_role("button", name="Añadir bloque").click()
    page.get_by_label("Nombre del bloque").fill("Tren superior")
    page.get_by_role("button", name="Añadir sub-bloque").click()

    # When I save without naming the sub-block, the API rejects it.
    page.get_by_role("button", name="Crear entrenamiento").click()
    expect(page.get_by_role("alert")).to_have_text("Algún bloque no es válido (nombre vacío).")


def test_removing_sub_block_returns_empty_state(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a block with one sub-block added.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    _go_to_new_form(page, app_url)
    page.get_by_role("button", name="Añadir bloque").click()
    page.get_by_role("button", name="Añadir sub-bloque").click()
    expect(page.get_by_label("Nombre del sub-bloque")).to_have_count(1)

    # When I remove it, the empty state returns.
    page.get_by_role("button", name="Eliminar sub-bloque").click()
    expect(page.get_by_label("Nombre del sub-bloque")).to_have_count(0)
    expect(page.get_by_text("Todavía no hay sub-bloques.")).to_be_visible()
