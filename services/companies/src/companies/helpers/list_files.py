"""What a pasted or uploaded list of candidates is refused for, before it's read."""

from pathlib import PurePath

from companies.constants.invites import (
    FILE_TOO_LARGE,
    LIST_FILE_TYPES,
    LIST_TOO_LONG,
    MAX_BULK_TEXT_LENGTH,
    MAX_UNREADABLE_SHARE,
    NOT_A_LIST_FILE,
)


def list_refusal(text: str, filename: str | None) -> str | None:
    """Why the list can't be read: a file that isn't a CSV or TXT file, or isn't text (a
    renamed spreadsheet), or is too large; a pasted list that's too long. None when it can."""
    if filename is None:
        return LIST_TOO_LONG if len(text) > MAX_BULK_TEXT_LENGTH else None

    if PurePath(filename).suffix.lower() not in LIST_FILE_TYPES or not looks_like_text(text):
        return NOT_A_LIST_FILE

    if len(text.encode()) > MAX_BULK_TEXT_LENGTH:
        return FILE_TOO_LARGE

    return None


def looks_like_text(text: str) -> bool:
    """No NUL bytes, and few characters the browser couldn't read (U+FFFD)."""
    return "\x00" not in text and text.count("\ufffd") <= MAX_UNREADABLE_SHARE * len(text)
