from collections.abc import Callable

from playwright.sync_api import Page, expect

from app.models import Exercise, User


def test_card_shows_thumbnail(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    upload_media: Callable[..., str],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an exercise with a thumbnail.
    admin = create_user(role="admin", email="admin@example.com")
    key = upload_media("thumbnail", "image/png")
    create_exercise(name="Con miniatura", type="gym", thumbnail_key=key)
    log_in_as(admin)

    # When the list loads.
    page.goto(f"{app_url}/ejercicios")

    # Then the card renders the thumbnail image (and it actually loads).
    img = page.get_by_role("article").filter(has_text="Con miniatura").locator("img")
    expect(img).to_be_visible()
    assert img.evaluate("el => el.naturalWidth") > 0


def test_detail_shows_video_player_when_video_present(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    upload_media: Callable[..., str],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an exercise with both a thumbnail and a video.
    admin = create_user(role="admin", email="admin@example.com")
    thumb = upload_media("thumbnail", "image/png")
    video = upload_media("video", "video/mp4")
    exercise = create_exercise(
        name="Con vídeo", type="pool", thumbnail_key=thumb, video_key=video
    )
    log_in_as(admin)

    # When the detail page loads.
    page.goto(f"{app_url}/ejercicios/{exercise.id}")

    # Then a video player is shown, using the thumbnail as its poster.
    video_el = page.locator("video")
    expect(video_el).to_be_visible()
    assert "/exercises/video/" in (video_el.get_attribute("src") or "")
    assert "/exercises/thumbnail/" in (video_el.get_attribute("poster") or "")


def test_detail_shows_thumbnail_when_no_video(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    create_exercise: Callable[..., Exercise],
    upload_media: Callable[..., str],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an exercise with only a thumbnail (no video).
    admin = create_user(role="admin", email="admin@example.com")
    thumb = upload_media("thumbnail", "image/png")
    exercise = create_exercise(name="Solo miniatura", type="gym", thumbnail_key=thumb)
    log_in_as(admin)

    # When the detail page loads.
    page.goto(f"{app_url}/ejercicios/{exercise.id}")

    # Then the thumbnail image is shown and there's no video player.
    expect(page.locator("section img")).to_be_visible()
    expect(page.locator("video")).not_to_be_visible()


def test_admin_uploads_thumbnail_when_creating(
    page: Page,
    app_url: str,
    create_user: Callable[..., User],
    log_in_as: Callable[[User], None],
) -> None:
    # Given an admin on the new-exercise form.
    admin = create_user(role="admin", email="admin@example.com")
    log_in_as(admin)
    page.goto(f"{app_url}/ejercicios")
    page.get_by_role("link", name="Nuevo ejercicio").click()
    page.get_by_label("Nombre").fill("Subida real")

    # When they pick a thumbnail file (uploaded straight to S3 via presign).
    png = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108020000009077"
        "53de0000000c4944415408d76360000002000154a24f5c0000000049454e44ae426082"
    )
    page.locator('input[type="file"]').first.set_input_files(
        files=[{"name": "thumb.png", "mimeType": "image/png", "buffer": png}]
    )
    # The preview image appears once the upload completes, and a remove control
    # confirms the field holds an uploaded object.
    expect(page.get_by_role("button", name="Quitar miniatura")).to_be_visible()
    page.get_by_role("button", name="Guardar ejercicio").click()

    # Then it's created and the thumbnail shows on its detail page.
    expect(page.get_by_role("status").filter(has_text="Ejercicio creado.")).to_be_visible()
    expect(page.get_by_role("heading", name="Subida real")).to_be_visible()
    expect(page.locator("section img")).to_be_visible()
