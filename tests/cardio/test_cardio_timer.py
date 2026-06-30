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


def _block(position: int, *, effort_seconds: int, repeats: int = 1) -> CardioItem:
    """A timed block with a single effort interval, repeated `repeats` times."""
    return CardioItem(
        kind=CardioItemKind.block,
        position=position,
        repeats=repeats,
        intervals=[
            CardioInterval(
                kind=CardioIntervalKind.effort,
                position=0,
                duration_seconds=effort_seconds,
                intensity_pct=100,
            )
        ],
    )


def test_timer_runs_through_blocks_to_the_finish(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_cardio_training: Callable[..., CardioTraining],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a two-block session with short efforts so the countdown advances fast.
    member = create_user(role="member", email="member@example.com")
    training = create_cardio_training(
        title="Series cortas",
        subtype="anaerobic",
        items=[_block(0, effort_seconds=1), _block(1, effort_seconds=1)],
    )
    log_in_as(member)

    # When I open the register page and start the timer.
    page.goto(f"{app_url}/entrenamientos/cardio/sesion/{training.id}/registrar")
    page.get_by_role("button", name="Iniciar crono").click()

    # The first block is shown, with its effort interval highlighted.
    expect(page.get_by_text("Bloque 1/2", exact=True)).to_be_visible()

    # The first block's effort completes → "Bloque 1/2 completado".
    expect(page.get_by_text("Bloque 1/2 completado")).to_be_visible()

    # Continuing runs the second (last) block, which ends the workout.
    page.get_by_role("button", name="Siguiente bloque").click()
    expect(page.get_by_text("Entrenamiento finalizado")).to_be_visible()

    # Closing the timer returns to the register form.
    page.get_by_role("button", name="Cerrar cronómetro").click()
    expect(page.get_by_role("button", name="Finalizar sesión")).to_be_visible()


def test_timer_sound_starts_muted_and_toggles(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_cardio_training: Callable[..., CardioTraining],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a running timer (a long effort so it stays on the running view).
    member = create_user(role="member", email="member@example.com")
    training = create_cardio_training(
        title="Con sonido",
        subtype="anaerobic",
        items=[_block(0, effort_seconds=60)],
    )
    log_in_as(member)

    page.goto(f"{app_url}/entrenamientos/cardio/sesion/{training.id}/registrar")
    page.get_by_role("button", name="Iniciar crono").click()

    # Sound starts muted: the toggle offers to turn it on, and reports not-pressed.
    unmute = page.get_by_role("button", name="Activar sonido")
    expect(unmute).to_be_visible()
    expect(unmute).to_have_attribute("aria-pressed", "false")

    # Toggling on flips the button to "Silenciar" and reports pressed.
    unmute.click()
    mute = page.get_by_role("button", name="Silenciar")
    expect(mute).to_be_visible()
    expect(mute).to_have_attribute("aria-pressed", "true")

    # Toggling back returns to the muted state.
    mute.click()
    expect(page.get_by_role("button", name="Activar sonido")).to_have_attribute(
        "aria-pressed", "false"
    )


def test_timer_button_hidden_without_timed_blocks(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_cardio_training: Callable[..., CardioTraining],
    log_in_as: Callable[[User], None],
) -> None:
    # Given a session with no blocks (nothing to time).
    member = create_user(role="member", email="member@example.com")
    training = create_cardio_training(title="Sin bloques", subtype="aerobic")
    log_in_as(member)

    page.goto(f"{app_url}/entrenamientos/cardio/sesion/{training.id}/registrar")
    expect(page.get_by_role("button", name="Iniciar crono")).to_have_count(0)
