import re
from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import (
    CardioInterval,
    CardioIntervalKind,
    CardioItem,
    CardioItemKind,
    CardioTraining,
    User,
)


def _example_training(
    create_cardio_training: Callable[..., CardioTraining],
) -> CardioTraining:
    """A training matching the user's example: a 4x block (round of efforts + a
    rest) with a trailing rest, followed by an inter-block note."""
    return create_cardio_training(
        title="Series umbral",
        subtype="aerobic",
        items=[
            CardioItem(
                kind=CardioItemKind.block,
                position=0,
                repeats=4,
                rest_seconds=60,
                intervals=[
                    CardioInterval(
                        kind=CardioIntervalKind.effort,
                        position=0,
                        duration_seconds=60,
                        intensity_pct=60,
                    ),
                    CardioInterval(
                        kind=CardioIntervalKind.effort,
                        position=1,
                        duration_seconds=180,
                        intensity_pct=80,
                    ),
                    CardioInterval(
                        kind=CardioIntervalKind.rest, position=2, duration_seconds=30
                    ),
                ],
            ),
            CardioItem(kind=CardioItemKind.note, position=1, text="10s descanso"),
        ],
    )


def test_category_page_shows_subtype_cards(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos/cardio")

    main = page.get_by_role("main")
    # exact — "Aeróbico" is a substring of "Anaeróbico".
    expect(main.get_by_role("heading", name="Aeróbico", exact=True)).to_be_visible()
    expect(main.get_by_role("heading", name="Anaeróbico", exact=True)).to_be_visible()
    expect(main.get_by_role("heading", name="Aláctico", exact=True)).to_be_visible()


def test_detail_renders_blocks_round_and_rest(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_cardio_training: Callable[..., CardioTraining],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    training = _example_training(create_cardio_training)
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos/cardio/sesion/{training.id}")

    main = page.get_by_role("main")
    expect(main.get_by_role("heading", name="Series umbral")).to_be_visible()
    expect(main.get_by_text("Repetir 4 veces")).to_be_visible()
    # The round's intervals, in order.
    items = main.get_by_role("listitem")
    expect(items.nth(0)).to_contain_text("1min · 60%")
    expect(items.nth(1)).to_contain_text("3min · 80%")
    expect(items.nth(2)).to_contain_text("30s descanso")
    # Trailing rest and the inter-block note.
    expect(main.get_by_text("Después: 1min de descanso")).to_be_visible()
    expect(main.get_by_text("10s descanso")).to_be_visible()


def test_admin_creates_cardio_training(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    page.goto(f"{app_url}/entrenamientos/cardio/aerobico/nuevo")

    # Scope is shown in the heading; no subtype picker.
    expect(page.get_by_role("heading", name="Nuevo entrenamiento · Cardio / Aeróbico")).to_be_visible()

    page.get_by_label("Título").fill("Mi sesión")
    page.get_by_role("button", name="Añadir bloque").click()
    page.get_by_label("Repeticiones del bloque").fill("3")
    # The new block starts with one effort interval — fill it.
    page.get_by_label("Duración").first.fill("2:00")
    page.get_by_label("Intensidad").first.fill("75")
    page.get_by_role("button", name="Crear entrenamiento").click()

    expect(page.get_by_role("status").filter(has_text="Entrenamiento creado.")).to_be_visible()
    expect(page).to_have_url(
        re.compile(rf"{re.escape(app_url)}/entrenamientos/cardio/sesion/[0-9a-f-]+$")
    )
    main = page.get_by_role("main")
    expect(main.get_by_role("heading", name="Mi sesión")).to_be_visible()
    expect(main.get_by_text("Repetir 3 veces")).to_be_visible()
    expect(main.get_by_role("listitem").first).to_contain_text("2min · 75%")


def test_edit_prefills_and_subtype_is_immutable(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_cardio_training: Callable[..., CardioTraining],
    log_in_as: Callable[[User], None],
) -> None:
    admin = create_user(role="admin", email="admin@example.com")
    training = _example_training(create_cardio_training)
    log_in_as(admin)
    page.goto(f"{app_url}/entrenamientos/cardio/sesion/{training.id}/editar")

    # Scope shown in the heading, not as editable fields.
    expect(page.get_by_role("heading", name="Editar entrenamiento · Cardio / Aeróbico")).to_be_visible()
    expect(page.get_by_label("Título")).to_have_value("Series umbral")
    expect(page.get_by_label("Repeticiones del bloque")).to_have_value("4")
    # mm:ss round-trip of the first effort.
    expect(page.get_by_label("Duración").first).to_have_value("1:00")

    # Change the title and save.
    page.get_by_label("Título").fill("Series editadas")
    page.get_by_role("button", name="Guardar cambios").click()
    expect(page.get_by_role("status").filter(has_text="Entrenamiento actualizado.")).to_be_visible()
    expect(page).to_have_url(f"{app_url}/entrenamientos/cardio/sesion/{training.id}")
    expect(page.get_by_role("main").get_by_role("heading", name="Series editadas")).to_be_visible()


def test_member_cannot_access_new_or_edit(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_cardio_training: Callable[..., CardioTraining],
    log_in_as: Callable[[User], None],
) -> None:
    member = create_user(role="member", email="member@example.com")
    training = _example_training(create_cardio_training)
    log_in_as(member)

    # New form: admin-guarded → redirected to the trainings list.
    page.goto(f"{app_url}/entrenamientos/cardio/aerobico/nuevo")
    expect(page.get_by_role("button", name="Crear entrenamiento")).not_to_be_visible()
    expect(page).to_have_url(f"{app_url}/entrenamientos")

    # Edit page: admin-guarded too.
    page.goto(f"{app_url}/entrenamientos/cardio/sesion/{training.id}/editar")
    expect(page.get_by_role("button", name="Guardar cambios")).not_to_be_visible()
    expect(page).to_have_url(f"{app_url}/entrenamientos")


def test_admin_deletes_cardio_training(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_cardio_training: Callable[..., CardioTraining],
    log_in_as: Callable[[User], None],
) -> None:
    admin = create_user(role="admin", email="admin@example.com")
    training = create_cardio_training(title="A borrar", subtype="aerobic")
    log_in_as(admin)
    page.goto(f"{app_url}/entrenamientos/cardio/sesion/{training.id}")

    page.get_by_role("button", name="Eliminar").click()
    dialog = page.get_by_role("dialog", name="Eliminar entrenamiento")
    expect(dialog).to_be_visible()
    dialog.get_by_role("button", name="Eliminar").click()

    expect(page.get_by_role("status").filter(has_text="Entrenamiento eliminado.")).to_be_visible()
    expect(page).to_have_url(f"{app_url}/entrenamientos/cardio")
    page.goto(f"{app_url}/entrenamientos/cardio/aerobico")
    expect(page.get_by_role("button", name="A borrar")).not_to_be_visible()
