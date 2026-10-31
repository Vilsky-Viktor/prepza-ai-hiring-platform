"""The team's notes as the bell, the digest and Slack show them: an excerpt on one line, a bell
item that grows with each note and names its latest authors, a deleted note or account taken
back out, and a Slack message that shows the note as written, never as markup, within Slack's
limit."""

from types import SimpleNamespace

import pytest

from notifications.constants.notes import GROUP_NOTES_KEPT, SLACK_TEXT_CHARS
from notifications.helpers.member_emails import digest_email
from notifications.helpers.member_selection import digest_sections
from notifications.helpers.notes import (
    authors_of,
    excerpt,
    first_item,
    with_note,
    without_author,
    without_note,
)
from notifications.helpers.slack import note_message

SITE = "https://testee.ai"


def note(note_id: str, author: str | None, **fields) -> dict:
    return {
        "note_id": note_id,
        "company_id": "c1",
        "interview_id": "i1",
        "title": "AI Engineer",
        "author_id": author,
        "author_name": author.title() if author else None,
        "text": "Shortlist the top 5",
        **fields,
    }


@pytest.mark.parametrize(
    ("text", "limit", "shown"),
    [
        ("Short", 160, "Short"),
        ("Two\n\nlines  here", 160, "Two lines here"),
        ("Call the top five candidates on Monday", 20, "Call the top five…"),
        ("x" * 30, 10, "x" * 9 + "…"),
    ],
)
def test_an_excerpt_is_one_line_cut_at_a_space_where_it_can_be(text, limit, shown):
    assert excerpt(text, limit) == shown


def test_a_bell_item_grows_with_each_note_and_names_its_latest_authors():
    item = first_item(note("n1", "ann"))
    item = with_note(item, note("n2", "bob"))
    item = with_note(item, note("n3", "ann", title="AI Engineer II"))

    assert (item["count"], item["title"], item["authors"]) == (3, "AI Engineer II", ["Ann", "Bob"])
    assert [entry["id"] for entry in item["notes"]] == ["n1", "n2", "n3"]


def test_a_bell_item_keeps_only_its_latest_notes_but_counts_them_all():
    item = first_item(note("n0", "ann"))

    for number in range(1, GROUP_NOTES_KEPT + 5):
        item = with_note(item, note(f"n{number}", "ann"))

    assert item["count"] == GROUP_NOTES_KEPT + 5
    assert len(item["notes"]) == GROUP_NOTES_KEPT


def test_a_deleted_note_or_account_leaves_the_item():
    item = with_note(first_item(note("n1", "ann")), note("n2", "bob"))

    assert without_note(item, "n1") == ([item["notes"][1]], 1)
    assert without_note(item, "other") == (item["notes"], 2)
    assert authors_of(without_author(item, "ann")) == ["Bob", None]


def test_a_slack_note_shows_who_wrote_it_where_and_its_text_as_written():
    message = note_message(note("n1", "ann", text="<!channel> *bold* at www.evil.com"), SITE)
    texts = [block["text"]["text"] for block in message["blocks"][:2]]

    assert message["text"] == "Ann added a note on “AI Engineer”:"
    assert texts[1] == "&lt;!channel&gt; *bold* at www.\u200bevil.\u200bcom"
    assert all(block["text"]["type"] == "plain_text" for block in message["blocks"][:2])
    assert message["blocks"][2]["elements"][0]["url"] == (
        f"{SITE}/companies/c1/interviews/i1?tab=notes"
    )


@pytest.mark.parametrize(
    ("author_id", "named"),
    [(None, "A former member"), ("key:k1", "A deleted API key")],
)
def test_a_slack_note_without_its_authors_name_says_what_they_were(author_id, named):
    message = note_message({**note("n1", None), "author_id": author_id, "title": None}, SITE)

    assert message["text"] == f"{named} added a note on an interview:"


def test_a_long_note_full_of_markup_fits_slacks_limit():
    message = note_message(note("n1", "ann", text="<" * 2000), SITE)
    shown = message["blocks"][1]["text"]["text"]

    assert len(shown) <= SLACK_TEXT_CHARS
    assert shown.endswith("…") and shown.startswith("&lt;")


def pending(note_id, interview_id, title, author, created, text="Note"):
    return SimpleNamespace(
        note_id=note_id,
        company_id="c1",
        interview_id=interview_id,
        title=title,
        author_id=author,
        author_name=author.title() if author else None,
        excerpt=text,
        created_at=created,
    )


COMPANIES = [{"id": "c1", "name": "Acme", "members": [{"user_id": "ann", "editor": True}]}]
# Newest first, as the digest reads them.
NOTES = [
    pending("n4", "i2", "Backend", "bob", 4, "Hire her"),
    pending("n3", "i1", "AI Engineer", None, 3, "From someone gone"),
    pending("n2", "i1", "AI Engineer", "ann", 2, "Mine"),
    pending("n1", "i1", "AI Engineer", "bob", 1, "Oldest"),
]
ON = {"note_added": True}


def test_the_digest_groups_others_notes_per_interview_with_the_latest_two():
    [(company, rows)] = digest_sections("ann", ON, COMPANIES, [], SITE, NOTES)
    link = f"{SITE}/companies/c1/interviews/{{}}?tab=notes"

    assert company == "Acme"
    # Ann's own note is left out; interviews by title.
    assert rows == [
        ("note_added", {"title": "AI Engineer", "count": 2}, link.format("i1")),
        ("note_by_former", {"excerpt": "From someone gone"}, link.format("i1")),
        ("note", {"author": "Bob", "excerpt": "Oldest"}, link.format("i1")),
        ("note_added", {"title": "Backend", "count": 1}, link.format("i2")),
        ("note", {"author": "Bob", "excerpt": "Hire her"}, link.format("i2")),
    ]


def test_no_notes_in_the_digest_with_its_setting_off_or_only_ones_own():
    assert digest_sections("ann", {"note_added": False}, COMPANIES, [], SITE, NOTES) == []
    assert digest_sections("ann", ON, COMPANIES, [], SITE, NOTES[2:3]) == []


@pytest.mark.parametrize("language", ["en", "ja", "ar"])
def test_the_digest_email_shows_each_interviews_notes_with_their_links(language):
    sections = digest_sections("ann", ON, COMPANIES, [], SITE, NOTES)
    recipient = {"user_id": "ann", "email": "ann@example.com", "language": language}
    email = digest_email(recipient, sections, SITE, "secret")
    link = f"{SITE}/companies/c1/interviews/i1?tab=notes"

    assert "Acme" in email.text
    assert all(text in email.text for text in ("Bob", "Oldest", "From someone gone", "Hire her"))
    # The count and the interview's title, and every line links to its interview's notes.
    assert "2" in email.text and "AI Engineer" in email.text
    assert link in email.text and f'href="{link}"' in email.html
    assert "Mine" not in email.text
