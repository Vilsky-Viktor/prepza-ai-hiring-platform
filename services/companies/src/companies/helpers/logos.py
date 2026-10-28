import io

from PIL import Image

from companies.constants.logos import (
    FORMATS,
    JPEG_TYPE,
    LOGO_PATH,
    LOGO_SIGNATURES,
    MAX_LOGO_BYTES,
    MAX_LOGO_SIDE,
    PNG_TYPE,
    WEBP_TYPE,
)
from companies.models.companies import Company


def logo_type(content: bytes) -> str | None:
    """The media type of a PNG, JPEG or WebP image no larger than MAX_LOGO_BYTES; None for
    anything else."""
    if not content or len(content) > MAX_LOGO_BYTES:
        return None

    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return WEBP_TYPE

    return next(
        (kind for signature, kind in LOGO_SIGNATURES if content.startswith(signature)), None
    )


def logo_path(company: Company | None) -> str | None:
    """The logo's address on the site, or None when the company has none."""
    if company is None or company.logo_type is None:
        return None

    return LOGO_PATH.format(company_id=company.id, version=company.logo_version)


def stored_logo(content: bytes, media_type: str) -> tuple[bytes, str] | None:
    """The logo as it's kept, decoded to check it really is that image: a PNG as PNG, a JPEG as
    JPEG (its quality kept), each without its metadata (a photo's camera and place); a WebP as
    PNG, transparency kept, since classic Outlook shows no WebP and the same logo goes into
    emails. None for an image that can't be read, isn't the type its first bytes claim, or is
    over MAX_LOGO_SIDE pixels a side, which is checked from its header before decoding. CPU
    work: call it in a thread."""
    out = io.BytesIO()

    try:
        image = Image.open(io.BytesIO(content))

        if image.format != FORMATS[media_type] or max(image.size) > MAX_LOGO_SIDE:
            return None

        if media_type == JPEG_TYPE:
            image.save(out, "JPEG", quality="keep")

            return out.getvalue(), JPEG_TYPE

        image.save(out, "PNG", optimize=True)
    except (OSError, ValueError, Image.DecompressionBombError):
        return None

    return out.getvalue(), PNG_TYPE
