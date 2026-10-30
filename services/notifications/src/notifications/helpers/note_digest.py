# The digest's lines about the team's notes: for each interview with notes the reader didn't
# write, how many, then the latest few (their author and start). Rows are (the template's line,
# the values that fill it, the page it links to).
from notifications.constants.notes import DIGEST_EXCERPTS, NOTES_LINK


def note_rows(user_id: str, notes: list, site: str) -> list:
    """One company's notes (pending_notes rows, newest first) as the user's lines, the
    interviews by title."""
    by_interview = {}

    for note in notes:
        if note.author_id != user_id:
            by_interview.setdefault(note.interview_id, []).append(note)

    rows = []

    for interview_notes in sorted(by_interview.values(), key=lambda found: title(found).lower()):
        latest = interview_notes[0]
        link = site + NOTES_LINK.format(
            company_id=latest.company_id, interview_id=latest.interview_id
        )
        count = {"title": title(interview_notes), "count": len(interview_notes)}
        rows.append(("note_added", count, link))
        rows += [excerpt_row(note, link) for note in interview_notes[:DIGEST_EXCERPTS]]

    return rows


def title(notes: list) -> str:
    """The interview's title, as its latest note named it."""
    return notes[0].title or ""


def excerpt_row(note, link: str) -> tuple:
    """A note's author and start; a former member's names neither."""
    if note.author_name:
        return ("note", {"author": note.author_name, "excerpt": note.excerpt}, link)

    return ("note_by_former", {"excerpt": note.excerpt}, link)
