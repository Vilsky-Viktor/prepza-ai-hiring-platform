import re

from notifications.constants.email import MAX_FILENAME_LENGTH, UNSAFE_FILENAME


def pdf_name(*parts: str) -> str:
    """A PDF's file name from its parts (a translated heading and a candidate or test name),
    joined by a dash, without characters that break a file name, and cut to
    MAX_FILENAME_LENGTH."""
    cleaned = [" ".join(re.sub(UNSAFE_FILENAME, " ", part).split()) for part in parts if part]
    name = " – ".join(part for part in cleaned if part)[:MAX_FILENAME_LENGTH].strip()

    return f"{name or 'report'}.pdf"
