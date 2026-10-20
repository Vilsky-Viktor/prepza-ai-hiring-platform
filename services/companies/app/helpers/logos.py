import io

from PIL import Image

from app.constants.logos import (
    LOGO_PATH,
    LOGO_SIGNATURES,
    MAX_LOGO_BYTES,
    MAX_LOGO_SIDE,
    PNG_TYPE,
    WEBP_TYPE,
)
from app.models.companies import Company


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


def for_email(content: bytes, media_type: str) -> tuple[bytes, str] | None:
    """A WebP logo as PNG, transparency kept: classic Outlook shows no WebP, and the same logo
    goes into emails. PNG and JPEG stay as they are. None for a WebP that can't be read or is
    over MAX_LOGO_SIDE pixels a side, which is checked from its header before decoding. CPU
    work: call it in a thread."""
    if media_type != WEBP_TYPE:
        return content, media_type

    out = io.BytesIO()

    try:
        image = Image.open(io.BytesIO(content))

        if max(image.size) > MAX_LOGO_SIDE:
            return None

        image.save(out, "PNG", optimize=True)
    except (OSError, Image.DecompressionBombError):
        return None

    return out.getvalue(), PNG_TYPE
