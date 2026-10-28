import re
import unicodedata

from library.constants.templates import FALLBACK_SLUG, RESERVED_SLUGS, SLUG_LENGTH


def slugify(title: str) -> str:
    """A readable URL part from a title: lowercase ASCII letters and digits joined by "-",
    accents dropped and at most SLUG_LENGTH characters."""
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_title.lower()).strip("-")
    slug = slug[:SLUG_LENGTH].rstrip("-")

    return slug or FALLBACK_SLUG


def unique_slug(base: str, taken: set[str]) -> str:
    """`base`, or the first of "base-2", "base-3"… that isn't taken or reserved."""
    slug = base
    number = 2

    while slug in taken or slug in RESERVED_SLUGS:
        slug = f"{base}-{number}"
        number += 1

    return slug
