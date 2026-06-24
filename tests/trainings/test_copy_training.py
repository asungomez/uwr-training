import re
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


def _note(text: str, position: int) -> TrainingItem:
    return TrainingItem(kind=TrainingItemKind.note, text=text, position=position)


def _training_with_content(create_training: Callable[..., TrainingSession]) -> TrainingSession:
    """A training with a title, a block, a sub-block, and two note items."""
    return create_training(
        title="Sesión original",
        category="gym",
        subtype="accumulation",
        blocks=[
            TrainingBlock(
                name="Calentamiento",
                position=0,
                sub_blocks=[
                    TrainingSubBlock(
                        name="Movilidad",
                        position=0,
                        notes="Sin prisa",
                        items=[_note("Rotaciones", 0), _note("Sentadillas", 1)],
                    )
                ],
            )
        ],
    )


def test_member_does_not_see_copy_button(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a member viewing a training's detail page.
    member = create_user(role="member", email="member@example.com")
    training = create_training(title="Sesión original", category="gym", subtype="accumulation")
    log_in_as(member)
    page.goto(f"{app_url}/entrenamientos/{training.id}")

    # Then there's no copy button.
    expect(page.get_by_role("link", name="Copiar entrenamiento")).to_have_count(0)


def test_admin_copy_button_opens_prepopulated_form(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an admin viewing a training that has content.
    admin = create_user(role="admin", email="admin@example.com")
    training = _training_with_content(create_training)
    log_in_as(admin)
    page.goto(f"{app_url}/entrenamientos/{training.id}")

    # When they click "Copiar entrenamiento".
    page.get_by_role("link", name="Copiar entrenamiento").click()

    # Then they land on the new-training form, carrying the source id in the URL.
    expect(page).to_have_url(f"{app_url}/entrenamientos/nuevo?copiar_de={training.id}")
    expect(page.get_by_role("heading", name="Nuevo entrenamiento")).to_be_visible()

    # And the form is pre-populated with the source training's data.
    expect(page.get_by_label("Título")).to_have_value("Sesión original")
    expect(page.get_by_label("Categoría")).to_have_value("gym")
    expect(page.get_by_label("Subtipo")).to_have_value("accumulation")
    expect(page.get_by_label("Nombre del bloque")).to_have_value("Calentamiento")
    expect(page.get_by_label("Nombre del sub-bloque")).to_have_value("Movilidad")
    notes = page.get_by_label("Nota", exact=True)
    expect(notes).to_have_count(2)
    expect(notes.nth(0)).to_have_value("Rotaciones")
    expect(notes.nth(1)).to_have_value("Sentadillas")


def test_copy_creates_a_separate_training(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_training: Callable[..., TrainingSession],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an admin on the pre-populated copy form.
    admin = create_user(role="admin", email="admin@example.com")
    training = _training_with_content(create_training)
    log_in_as(admin)
    page.goto(f"{app_url}/entrenamientos/nuevo?copiar_de={training.id}")

    # When they tweak the title and submit.
    page.get_by_label("Título").fill("Sesión copiada")
    page.get_by_role("button", name="Crear entrenamiento").click()

    # Then a new training is created at a distinct URL (not the source's).
    expect(page.get_by_role("status").filter(has_text="Entrenamiento creado.")).to_be_visible()
    expect(page).to_have_url(re.compile(rf"{re.escape(app_url)}/entrenamientos/[0-9a-f-]+$"))
    expect(page).not_to_have_url(f"{app_url}/entrenamientos/{training.id}")

    # The copy keeps the source's content.
    main = page.get_by_role("main")
    expect(main.get_by_role("heading", name="Sesión copiada")).to_be_visible()
    expect(main.get_by_role("heading", name="Calentamiento")).to_be_visible()
    expect(main.get_by_text("Rotaciones")).to_be_visible()


def test_copy_unknown_id_shows_not_found(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an admin opening the copy form for a non-existent training.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    page.goto(f"{app_url}/entrenamientos/nuevo?copiar_de=00000000-0000-0000-0000-000000000000")

    # Then a not-found message shows instead of the form.
    expect(page.get_by_text("No se ha encontrado el entrenamiento a copiar.")).to_be_visible()
    expect(page.get_by_role("button", name="Crear entrenamiento")).to_have_count(0)
