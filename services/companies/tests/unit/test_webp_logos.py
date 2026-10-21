import base64
import io

from PIL import Image

from app.constants.logos import MAX_LOGO_SIDE
from app.helpers import logos
from tests.unit.test_logos import COMPANY_ID, company, sign_in  # noqa: F401 (fixture)

URL = f"/companies/{COMPANY_ID}/logo"


def webp(mode="RGBA", size=(4, 4)) -> bytes:
    out = io.BytesIO()
    Image.new(mode, size, (200, 30, 30, 128) if mode == "RGBA" else (200, 30, 30)).save(
        out, "WEBP", lossless=True
    )

    return out.getvalue()


def test_a_webp_logo_is_kept_as_png_with_its_transparency(client, company):  # noqa: F811
    _, saved = company
    sign_in("bob")

    response = client.put(URL, json={"image": base64.b64encode(webp()).decode()})

    assert response.status_code == 200
    content, media_type = saved["logo"]
    assert media_type == "image/png"
    stored = Image.open(io.BytesIO(content))
    assert (stored.format, stored.mode) == ("PNG", "RGBA")
    assert stored.getpixel((0, 0)) == (200, 30, 30, 128)


def test_a_webp_that_cant_be_read_is_refused(client, company):  # noqa: F811
    _, saved = company
    sign_in("bob")
    broken = base64.b64encode(b"RIFF\x00\x00\x00\x00WEBPVP8 broken").decode()

    assert client.put(URL, json={"image": broken}).status_code == 422
    assert saved == {}


def test_a_webp_too_many_pixels_wide_is_refused_without_decoding_it(client, company):  # noqa: F811
    _, saved = company
    sign_in("bob")
    wide = webp(size=(MAX_LOGO_SIDE + 1, 1))

    assert client.put(URL, json={"image": base64.b64encode(wide).decode()}).status_code == 422
    assert saved == {}


def test_a_decompression_bomb_is_refused_not_an_error(client, company, monkeypatch):  # noqa: F811
    _, saved = company
    sign_in("bob")

    def bomb(_file):
        raise Image.DecompressionBombError("too many pixels")

    monkeypatch.setattr(logos.Image, "open", bomb)

    assert client.put(URL, json={"image": base64.b64encode(webp()).decode()}).status_code == 422
    assert saved == {}


def test_a_file_that_only_starts_like_a_png_or_jpeg_is_refused(client, company):  # noqa: F811
    _, saved = company
    sign_in("bob")

    for fake in (b"\x89PNG\r\n\x1a\n" + b"<script>", b"\xff\xd8\xff" + b"<html>"):
        response = client.put(URL, json={"image": base64.b64encode(fake).decode()})

        assert response.status_code == 422

    assert saved == {}


def test_a_png_too_many_pixels_wide_is_refused(client, company):  # noqa: F811
    _, saved = company
    sign_in("bob")
    out = io.BytesIO()
    Image.new("1", (MAX_LOGO_SIDE + 1, 1)).save(out, "PNG")

    assert (
        client.put(URL, json={"image": base64.b64encode(out.getvalue()).decode()}).status_code
        == 422
    )
    assert saved == {}


def test_a_jpeg_logo_is_kept_as_jpeg_without_its_photos_metadata(client, company):  # noqa: F811
    _, saved = company
    sign_in("bob")
    exif = Image.Exif()
    exif[0x010F] = "Camera maker"
    out = io.BytesIO()
    Image.new("RGB", (8, 8), (0, 90, 200)).save(out, "JPEG", exif=exif.tobytes())

    response = client.put(URL, json={"image": base64.b64encode(out.getvalue()).decode()})

    assert response.status_code == 200
    content, media_type = saved["logo"]
    stored = Image.open(io.BytesIO(content))
    assert (media_type, stored.format) == ("image/jpeg", "JPEG")
    assert dict(stored.getexif()) == {}
