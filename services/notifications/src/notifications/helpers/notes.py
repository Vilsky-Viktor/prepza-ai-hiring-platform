# The team's notes as the bell and the digest show them. A bell item's data: the company and
# interview, the interview's title, how many notes it groups (`count`), its latest notes (`notes`:
# [{"id", "author_id", "author"}], oldest first, at most GROUP_NOTES_KEPT) and their latest
# authors (`authors`: names, newest first, None for a former member).
import re

from notifications.constants.notes import AUTHORS_SHOWN, EXCERPT_CHARS, GROUP_NOTES_KEPT


def excerpt(text: str, limit: int = EXCERPT_CHARS) -> str:
    """The note's start on one line: at most `limit` characters, cut at a space where it can be,
    with an ellipsis when cut."""
    flat = re.sub(r"\s+", " ", text).strip()

    if len(flat) <= limit:
        return flat

    cut = flat[: limit - 1]
    space = cut.rfind(" ")

    return (cut[:space] if space > limit // 2 else cut).rstrip() + "…"


def authors_of(notes: list[dict]) -> list[str | None]:
    """The latest notes' authors, newest first, each once, at most AUTHORS_SHOWN."""
    authors = []
    seen = set()

    for note in reversed(notes):
        if note["author_id"] in seen:
            continue

        seen.add(note["author_id"])
        authors.append(note["author"])

        if len(authors) == AUTHORS_SHOWN:
            break

    return authors


def first_item(note: dict) -> dict:
    """A new bell item with one note."""
    notes = [{"id": note["note_id"], "author_id": note["author_id"], "author": note["author_name"]}]

    return {
        "company_id": note["company_id"],
        "interview_id": note["interview_id"],
        "title": note["title"],
        "count": 1,
        "notes": notes,
        "authors": authors_of(notes),
    }


def with_note(data: dict, note: dict) -> dict:
    """A bell item with one more note, named as the interview is now."""
    added = first_item(note)
    notes = [*data.get("notes", []), *added["notes"]][-GROUP_NOTES_KEPT:]

    return {
        **data,
        "title": note["title"],
        "count": data.get("count", 1) + 1,
        "notes": notes,
        "authors": authors_of(notes),
    }


def without_note(data: dict, note_id: str) -> tuple[list[dict], int]:
    """A bell item's notes and count once the note is deleted."""
    notes = [note for note in data.get("notes", []) if note["id"] != note_id]

    return notes, data.get("count", 1) - (len(data.get("notes", [])) - len(notes))


def without_author(data: dict, author_id: str) -> list[dict]:
    """A bell item's notes, the deleted account's shown as a former member's."""
    return [
        {**note, "author_id": None, "author": None} if note["author_id"] == author_id else note
        for note in data.get("notes", [])
    ]
