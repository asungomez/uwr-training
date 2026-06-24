from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import Exercise, ExerciseRelation, User

SEARCH_PLACEHOLDER = "Buscar ejercicio a relacionar…"


def test_detail_shows_related_exercises(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an exercise with two related exercises (seeded directly).
    admin = create_user(role="admin", email="admin@example.com")
    inversa = create_exercise(name="Dominada inversa", type="gym")
    jalon = create_exercise(name="Jalón al pecho", type="gym")
    owner = create_exercise(
        name="Dominada prona",
        type="gym",
        related=[
            ExerciseRelation(
                related_exercise_id=inversa.id, note="Practica la segunda mitad", position=0
            ),
            ExerciseRelation(
                related_exercise_id=jalon.id, note="Si no tienes barra", position=1
            ),
        ],
    )
    log_in_as(admin)

    # When the detail page loads.
    page.goto(f"{app_url}/ejercicios/{owner.id}")

    # Then the related section lists both, each linking to its detail, with its note.
    section = page.get_by_role("list").filter(has_text="Dominada inversa")
    expect(page.get_by_role("heading", name="Ejercicios alternativos")).to_be_visible()
    expect(section.get_by_role("link", name="Dominada inversa")).to_have_attribute(
        "href", f"/ejercicios/{inversa.id}"
    )
    expect(page.get_by_text("Practica la segunda mitad")).to_be_visible()
    expect(page.get_by_text("Si no tienes barra")).to_be_visible()


def test_detail_hides_related_section_when_empty(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an exercise with no related exercises.
    admin = create_user(role="admin", email="admin@example.com")
    exercise = create_exercise(name="Sentadilla", type="gym")
    log_in_as(admin)

    # When the detail page loads, the related section is not shown.
    page.goto(f"{app_url}/ejercicios/{exercise.id}")
    expect(page.get_by_role("heading", name="Sentadilla")).to_be_visible()
    expect(page.get_by_role("heading", name="Ejercicios alternativos")).not_to_be_visible()


def test_related_exercise_thumbnail_shown(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    upload_media: Callable[..., str],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a related exercise that has a thumbnail.
    admin = create_user(role="admin", email="admin@example.com")
    thumb_key = upload_media("thumbnail", "image/png")
    target = create_exercise(name="Jalón al pecho", type="gym", thumbnail_key=thumb_key)
    owner = create_exercise(
        name="Dominada prona",
        type="gym",
        related=[ExerciseRelation(related_exercise_id=target.id, note="Alternativa", position=0)],
    )
    log_in_as(admin)

    # When the detail page loads, the related row shows the target's thumbnail.
    page.goto(f"{app_url}/ejercicios/{owner.id}")
    related_item = page.get_by_role("listitem").filter(has_text="Jalón al pecho")
    img = related_item.locator("img")
    expect(img).to_be_visible()
    assert img.evaluate("el => el.naturalWidth") > 0


def test_admin_adds_related_exercise_when_creating(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an existing exercise to relate to.
    admin = create_user(role="admin", email="admin@example.com")
    create_exercise(name="Jalón al pecho", type="gym")
    log_in_as(admin)
    page.goto(f"{app_url}/ejercicios")

    # When creating a new exercise and adding a related one via search.
    page.get_by_role("link", name="Nuevo ejercicio").click()
    page.get_by_label("Nombre").fill("Dominada prona")
    page.get_by_placeholder(SEARCH_PLACEHOLDER).fill("Jalón")
    page.get_by_role("button", name="Jalón al pecho", exact=True).click()
    page.get_by_placeholder("Nota (cuándo o por qué usar esta alternativa)…").fill(
        "Si no tienes barra"
    )
    page.get_by_role("button", name="Guardar ejercicio").click()

    # Then it's created and the relation shows on its detail page.
    expect(page.get_by_role("status").filter(has_text="Ejercicio creado.")).to_be_visible()
    expect(page.get_by_role("heading", name="Dominada prona")).to_be_visible()
    expect(page.get_by_role("heading", name="Ejercicios alternativos")).to_be_visible()
    expect(page.get_by_role("link", name="Jalón al pecho")).to_be_visible()
    expect(page.get_by_text("Si no tienes barra")).to_be_visible()


def test_edit_prefills_and_removes_related(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an exercise with a related exercise.
    admin = create_user(role="admin", email="admin@example.com")
    target = create_exercise(name="Jalón al pecho", type="gym")
    create_exercise(
        name="Dominada prona",
        type="gym",
        related=[ExerciseRelation(related_exercise_id=target.id, note="Si no tienes barra", position=0)],
    )
    log_in_as(admin)
    page.goto(f"{app_url}/ejercicios")

    # When editing, the existing relation is pre-filled.
    page.get_by_role("link", name="Editar Dominada prona").click()
    expect(page.get_by_text("Jalón al pecho")).to_be_visible()
    expect(
        page.get_by_placeholder("Nota (cuándo o por qué usar esta alternativa)…")
    ).to_have_value("Si no tienes barra")

    # When I remove it and save.
    page.get_by_role("button", name="Quitar Jalón al pecho").click()
    page.get_by_role("button", name="Guardar ejercicio").click()

    # Then it lands on the detail page, which no longer shows a related section.
    expect(page.get_by_role("status").filter(has_text="Ejercicio actualizado.")).to_be_visible()
    expect(page.get_by_role("heading", name="Dominada prona")).to_be_visible()
    expect(page.get_by_role("heading", name="Ejercicios alternativos")).not_to_be_visible()


def test_cannot_relate_exercise_to_itself(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an exercise being edited.
    admin = create_user(role="admin", email="admin@example.com")
    create_exercise(name="Dominada prona", type="gym")
    log_in_as(admin)
    page.goto(f"{app_url}/ejercicios")
    page.get_by_role("link", name="Editar Dominada prona").click()

    # When I search in the related-exercise picker, the exercise itself is excluded.
    page.get_by_placeholder(SEARCH_PLACEHOLDER).fill("Dominada")
    expect(page.get_by_text("No hay ejercicios que coincidan.")).to_be_visible()
