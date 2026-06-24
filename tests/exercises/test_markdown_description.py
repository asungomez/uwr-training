from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import Exercise, User

MARKDOWN = (
    "## Calentamiento\n\n"
    "- Movilidad articular\n"
    "- Respiraciones\n\n"
    "Mantén la **cadera neutra**. Consulta la [técnica](https://example.com)."
)


def test_detail_renders_markdown_as_html(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an exercise whose description is markdown.
    admin = create_user(role="admin", email="admin@example.com")
    exercise = create_exercise(name="Sentadilla", description=MARKDOWN, type="gym")
    log_in_as(admin)

    # When I open its detail page.
    page.goto(f"{app_url}/ejercicios/{exercise.id}")

    # Then the markdown renders as real HTML, not raw text.
    expect(page.get_by_role("heading", name="Calentamiento")).to_be_visible()
    expect(page.get_by_role("listitem").filter(has_text="Movilidad articular")).to_be_visible()
    expect(page.locator("strong", has_text="cadera neutra")).to_be_visible()
    link = page.get_by_role("link", name="técnica")
    expect(link).to_have_attribute("href", "https://example.com")
    # The raw markup must not leak as visible text.
    expect(page.get_by_text("## Calentamiento")).not_to_be_visible()


def test_create_with_markdown_editor_round_trips(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an admin opening the new-exercise form.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    page.goto(f"{app_url}/ejercicios")
    page.get_by_role("link", name="Nuevo ejercicio").click()

    # When I fill the name and type into the WYSIWYG editor, then save.
    page.get_by_label("Nombre").fill("Plancha")
    editor = page.get_by_role("textbox").nth(1)  # 0 = name input, 1 = MDXEditor
    editor.click()
    editor.type("Aguanta la posición durante un minuto.")
    page.get_by_role("button", name="Guardar ejercicio").click()

    # Then it's created and lands on its detail page, which shows the typed
    # description (the editor round-tripped the text through markdown).
    expect(page.get_by_role("status").filter(has_text="Ejercicio creado.")).to_be_visible()
    expect(page.get_by_role("heading", name="Plancha")).to_be_visible()
    expect(page.get_by_text("Aguanta la posición durante un minuto.")).to_be_visible()
