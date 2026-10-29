"""An interview's notes, against the real database: every member writes them; each edits only
their own; the author, the owner and admins delete; the owner and admins pin one at a time; a
note outlives its author's membership, shown as a former member's."""

import uuid

import pytest
from fastapi import HTTPException

from companies.constants.interview_notes import (
    NOTE_NOT_FOUND,
    ONLY_AUTHOR_DELETES,
    ONLY_AUTHOR_EDITS,
    ONLY_EDITORS_PIN,
)
from companies.integrations import accounts
from companies.repositories import members
from companies.services import interview_notes
from tests.integration import factories
from tests.integration.factories import as_member
from tests.integration.transactions import transaction


@pytest.fixture(autouse=True)
def names(monkeypatch):
    """Accounts is another service: the names it knows, by user id (the others go by email)."""
    known = {}

    async def profiles(user_ids):
        return {uid: known[uid] for uid in user_ids if uid in known}

    monkeypatch.setattr(accounts, "profiles", profiles)

    return known


async def write(team, role: str, text: str):
    interview, company, member = await as_member(getattr(team, role), team.interview.id)

    return await interview_notes.add(interview, company, member, text)


async def listed(team, role: str):
    interview, _, member = await as_member(getattr(team, role), team.interview.id)

    return await interview_notes.page(interview, member, 0, 20)


async def refusal(call) -> tuple[int, str]:
    with pytest.raises(HTTPException) as refused:
        await call

    return refused.value.status_code, refused.value.detail


def test_every_member_writes_and_each_sees_what_they_may_do(run, names):
    async def scenario():
        team = await factories.team("notes")
        names[team.owner] = {"name": "Olga Owner", "photo_url": "https://example.com/olga.png"}

        for role in ("owner", "admin", "viewer"):
            await write(team, role, f"From the {role}")

        outsider = await refusal(as_member(f"outsider-{uuid.uuid4()}", team.interview.id))

        return team, await listed(team, "viewer"), await listed(team, "admin"), outsider

    team, as_viewer, as_admin, outsider = run(scenario())

    # Newest first.
    assert [note.text for note in as_viewer] == [
        "From the viewer",
        "From the admin",
        "From the owner",
    ]
    assert [(note.author.name, note.author.photo_url) for note in as_viewer] == [
        (f"{team.viewer}@example.com", None),
        (f"{team.admin}@example.com", None),
        ("Olga Owner", "https://example.com/olga.png"),
    ]
    assert [(n.can_edit, n.can_delete, n.can_pin) for n in as_viewer] == [
        (True, True, False),
        (False, False, False),
        (False, False, False),
    ]
    assert [(n.can_edit, n.can_delete, n.can_pin) for n in as_admin] == [
        (False, True, True),
        (True, True, True),
        (False, True, True),
    ]
    assert outsider == (404, "Company not found")


@pytest.mark.parametrize(
    ("author", "editor", "allowed"),
    [("owner", "owner", True), ("viewer", "viewer", True), ("viewer", "owner", False)]
    + [("owner", "admin", False), ("admin", "viewer", False)],
)
def test_only_the_author_edits_a_note(run, author, editor, allowed):
    async def scenario():
        team = await factories.team("edits")
        note = await write(team, author, "First take")
        interview, company, member = await as_member(getattr(team, editor), team.interview.id)
        call = interview_notes.edit(interview, company, member, note.id, "Second take")
        outcome = await call if allowed else await refusal(call)

        return outcome, await listed(team, "owner")

    outcome, notes = run(scenario())

    if allowed:
        assert (outcome.text, outcome.edited_at is not None) == ("Second take", True)
        assert [note.text for note in notes] == ["Second take"]
    else:
        assert outcome == (403, ONLY_AUTHOR_EDITS)
        assert [(note.text, note.edited_at) for note in notes] == [("First take", None)]


@pytest.mark.parametrize(
    ("author", "deleter", "allowed"),
    [("viewer", "viewer", True), ("viewer", "admin", True), ("admin", "owner", True)]
    + [("owner", "admin", True), ("owner", "viewer", False), ("admin", "viewer", False)],
)
def test_the_author_the_owner_and_admins_delete_a_note(run, author, deleter, allowed):
    async def scenario():
        team = await factories.team("deletes")
        note = await write(team, author, "To delete")
        interview, company, member = await as_member(getattr(team, deleter), team.interview.id)
        call = interview_notes.delete(interview, company, member, note.id)
        outcome = await call if allowed else await refusal(call)

        return outcome, await listed(team, "owner")

    outcome, notes = run(scenario())

    assert outcome == (None if allowed else (403, ONLY_AUTHOR_DELETES))
    assert [note.text for note in notes] == ([] if allowed else ["To delete"])


def test_one_note_is_pinned_at_a_time_by_the_owner_or_an_admin(run):
    async def scenario():
        team = await factories.team("pins")
        first = await write(team, "viewer", "Strong on SQL")
        second = await write(team, "admin", "Weak on design")
        await write(team, "owner", "Newest")
        steps = []

        async def pin(role: str, note, pinned: bool):
            interview, company, member = await as_member(getattr(team, role), team.interview.id)
            await interview_notes.pin(interview, company, member, note.id, pinned)
            notes = await listed(team, "viewer")
            steps.append([(note.text, note.pinned) for note in notes])

        viewer = await refusal(pin("viewer", first, True))
        await pin("admin", first, True)
        await pin("owner", second, True)
        await pin("owner", second, False)

        return viewer, steps

    viewer, steps = run(scenario())

    assert viewer == (403, ONLY_EDITORS_PIN)
    # The pinned note first, then newest first; pinning another unpins the first.
    assert steps == [
        [("Strong on SQL", True), ("Newest", False), ("Weak on design", False)],
        [("Weak on design", True), ("Newest", False), ("Strong on SQL", False)],
        [("Newest", False), ("Weak on design", False), ("Strong on SQL", False)],
    ]


def test_a_note_of_another_interview_isnt_found(run):
    async def scenario():
        team = await factories.team("elsewhere")
        other = await factories.team("elsewhere")
        note = await write(other, "owner", "Not yours")
        interview, company, member = await as_member(team.owner, team.interview.id)

        return [
            await refusal(interview_notes.edit(interview, company, member, note.id, "Mine")),
            await refusal(interview_notes.delete(interview, company, member, note.id)),
            await refusal(interview_notes.pin(interview, company, member, note.id, True)),
        ]

    assert run(scenario()) == [(404, NOTE_NOT_FOUND)] * 3


def test_a_note_outlives_its_authors_membership_as_a_former_members(run, names):
    async def scenario():
        team = await factories.team("former")
        names[team.admin] = {"name": "Ada Admin", "photo_url": "https://example.com/ada.png"}
        await write(team, "admin", "Left behind")
        _, _, member = await as_member(team.admin, team.interview.id)
        await transaction(members.remove, member.id)

        return await listed(team, "owner")

    [note] = run(scenario())

    assert note.text == "Left behind"
    assert (note.author.former, note.author.name, note.author.photo_url) == (True, None, None)
    assert (note.can_edit, note.can_delete, note.can_pin) == (False, True, True)
