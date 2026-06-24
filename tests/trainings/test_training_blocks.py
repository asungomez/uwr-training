from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import TrainingBlock, TrainingSession, User


def _go_to_new_form(page: Page, app_url: str) -> None:
    # Category + subtype come from the URL now, not form fields.
    page.goto(f"{app_url}/entrenamientos/gimnasio/acumulacion/nuevo")
    page.get_by_label("Título").fill("Sesión con bloques")


# ---------------------------------------------------------------- happy paths


def test_admin_creates_training_with_blocks(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given the new-training form.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    _go_to_new_form(page, app_url)

    # When I add two named blocks and save.
    page.get_by_role("button", name="Añadir bloque").click()
    page.get_by_role("button", name="Añadir bloque").click()
    names = page.get_by_label("Nombre del bloque")
    names.nth(0).fill("Calentamiento")
    names.nth(1).fill("Tren superior")
    page.get_by_role("button", name="Crear entrenamiento").click()

    # Then it's created and lands on the detail page.
    expect(page.get_by_role("status").filter(has_text="Entrenamiento creado.")).to_be_visible()
    expect(page.get_by_role("heading", name="Sesión con bloques")).to_be_visible()


def test_blocks_start_expanded_and_can_collapse_all(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given two freshly added blocks.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    _go_to_new_form(page, app_url)
    page.get_by_role("button", name="Añadir bloque").click()
    page.get_by_role("button", name="Añadir bloque").click()

    # New blocks start expanded: a "Colapsar todo" control is offered, not "Expandir todo".
    expect(page.get_by_role("button", name="Colapsar todo")).to_be_visible()
    expect(page.get_by_role("button", name="Expandir todo")).not_to_be_visible()
    # Each block's expanded body is visible (its "Añadir sub-bloque" action shows).
    expect(page.get_by_role("button", name="Añadir sub-bloque")).to_have_count(2)

    # When I collapse all.
    page.get_by_role("button", name="Colapsar todo").click()

    # Then only "Expandir todo" remains and the bodies are hidden.
    expect(page.get_by_role("button", name="Expandir todo")).to_be_visible()
    expect(page.get_by_role("button", name="Colapsar todo")).not_to_be_visible()
    expect(page.get_by_role("button", name="Añadir sub-bloque")).to_have_count(0)


def test_mixed_collapse_state_shows_both_controls(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given two blocks, with only the first collapsed.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    _go_to_new_form(page, app_url)
    page.get_by_role("button", name="Añadir bloque").click()
    page.get_by_role("button", name="Añadir bloque").click()
    page.get_by_role("button", name="Colapsar bloque").first.click()

    # Then both collapse-all and expand-all controls are offered.
    expect(page.get_by_role("button", name="Colapsar todo")).to_be_visible()
    expect(page.get_by_role("button", name="Expandir todo")).to_be_visible()


def test_edit_prefills_blocks_and_persists_changes(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a training with two blocks.
    admin = create_user(role="admin", email="admin@example.com")
    training = create_training(
        title="Editable",
        category="gym",
        subtype="accumulation",
        blocks=[
            TrainingBlock(name="Calentamiento", position=0),
            TrainingBlock(name="Tren superior", position=1),
        ],
    )
    log_in_as(admin)
    page.goto(f"{app_url}/entrenamientos/{training.id}/editar")

    # The existing blocks are pre-filled.
    names = page.get_by_label("Nombre del bloque")
    expect(names).to_have_count(2)
    expect(names.nth(0)).to_have_value("Calentamiento")
    expect(names.nth(1)).to_have_value("Tren superior")

    # When I rename one, remove the other, add a new one, and save.
    names.nth(0).fill("Movilidad")
    page.get_by_role("button", name="Eliminar bloque").nth(1).click()
    page.get_by_role("button", name="Añadir bloque").click()
    page.get_by_label("Nombre del bloque").nth(1).fill("Core")
    page.get_by_role("button", name="Guardar cambios").click()
    expect(page.get_by_role("status").filter(has_text="Entrenamiento actualizado.")).to_be_visible()

    # Then the changes round-trip: reopening edit shows the new set.
    page.goto(f"{app_url}/entrenamientos/{training.id}/editar")
    edited = page.get_by_label("Nombre del bloque")
    expect(edited).to_have_count(2)
    expect(edited.nth(0)).to_have_value("Movilidad")
    expect(edited.nth(1)).to_have_value("Core")


def test_reorder_blocks_with_keyboard_persists(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a training with two ordered blocks.
    admin = create_user(role="admin", email="admin@example.com")
    training = create_training(
        title="Reordenable",
        category="gym",
        subtype="accumulation",
        blocks=[
            TrainingBlock(name="Primero", position=0),
            TrainingBlock(name="Segundo", position=1),
        ],
    )
    log_in_as(admin)
    page.goto(f"{app_url}/entrenamientos/{training.id}/editar")
    expect(page.get_by_label("Nombre del bloque")).to_have_count(2)

    # When I drag the first block's handle below the second. dnd-kit needs the
    # PointerSensor's 5px activation threshold crossed, plus intermediate moves so
    # the collision detection registers the drop target.
    handles = page.get_by_role("button", name="Reordenar bloque")
    source = handles.nth(0).bounding_box()
    target = handles.nth(1).bounding_box()
    assert source is not None and target is not None
    page.mouse.move(source["x"] + source["width"] / 2, source["y"] + source["height"] / 2)
    page.mouse.down()
    # A small first move crosses the activation distance; then move past the target.
    page.mouse.move(source["x"] + 5, source["y"] + 15)
    page.mouse.move(target["x"] + target["width"] / 2, target["y"] + target["height"] + 10, steps=10)
    page.mouse.up()

    # The order updates in place before saving.
    names = page.get_by_label("Nombre del bloque")
    expect(names.nth(0)).to_have_value("Segundo")
    expect(names.nth(1)).to_have_value("Primero")

    page.get_by_role("button", name="Guardar cambios").click()
    expect(page.get_by_role("status").filter(has_text="Entrenamiento actualizado.")).to_be_visible()

    # Then the new order persists after reload.
    page.goto(f"{app_url}/entrenamientos/{training.id}/editar")
    reloaded = page.get_by_label("Nombre del bloque")
    expect(reloaded.nth(0)).to_have_value("Segundo")
    expect(reloaded.nth(1)).to_have_value("Primero")


# ------------------------------------------------------------ not-so-happy paths


def test_blank_block_name_blocks_save(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given the new-training form with an empty block added.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    _go_to_new_form(page, app_url)
    page.get_by_role("button", name="Añadir bloque").click()

    # When I save without naming the block, the API rejects it.
    page.get_by_role("button", name="Crear entrenamiento").click()
    expect(page.get_by_role("alert")).to_have_text("Algún bloque no es válido (nombre vacío).")


def test_removing_block_drops_it(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a single added block.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    _go_to_new_form(page, app_url)
    page.get_by_role("button", name="Añadir bloque").click()
    expect(page.get_by_label("Nombre del bloque")).to_have_count(1)

    # When I remove it, the empty state returns.
    page.get_by_role("button", name="Eliminar bloque").click()
    expect(page.get_by_label("Nombre del bloque")).to_have_count(0)
    expect(page.get_by_text("Todavía no hay bloques.")).to_be_visible()


def test_member_cannot_reach_block_editor(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a member and an existing training.
    member = create_user(role="member", email="member@example.com")
    training = create_training(title="Privado", category="gym", subtype="accumulation")
    log_in_as(member)

    # When they try the edit URL directly, the admin guard redirects them away.
    page.goto(f"{app_url}/entrenamientos/{training.id}/editar")
    expect(page.get_by_role("button", name="Añadir bloque")).not_to_be_visible()
    expect(page).to_have_url(f"{app_url}/entrenamientos")
