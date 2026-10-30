"""The team's notes in the bell, against the real database: every member but the author gets
one item per interview while it's unread, which grows with each note; a redelivered event, a
deleted note (before or after its own event), a deleted interview, company or account, and a
member who left are each handled."""

import uuid

from event_pushes import push
from sqlalchemy import select

from notifications.core.db import Session
from notifications.models.notifications import Notification
from notifications.services import feed, notices
from tests.integration.factories import api, company
from tests.integration.note_events import created, deleted, note


async def deliver(*events: tuple) -> list[int]:
    """Pub/Sub's pushes of (type, data, event id), one after another; their answers."""
    async with api() as client:
        return [
            (await client.post("/internal/events", json=push(*event))).status_code
            for event in events
        ]


async def items(user_id: str) -> list[dict]:
    """The user's note items, newest first, as (count, authors, note ids)."""
    async with Session() as session:
        rows = await session.scalars(
            select(Notification)
            .where(Notification.recipient_id == user_id, Notification.kind == "note_added")
            .order_by(Notification.created_at.desc())
        )

        return [
            (row.data["count"], row.data["authors"], [n["id"] for n in row.data["notes"]])
            for row in rows
        ]


def test_members_but_the_author_get_one_item_per_interview_while_its_unread(run, teams):
    company_id, interview_id = company(), str(uuid.uuid4())
    ann, bob, cat = (f"{name}-{uuid.uuid4()}" for name in ("ann", "bob", "cat"))
    teams[company_id] = [ann, bob, cat]
    first = note(company_id, interview_id, ann, "Shortlist the top 5", author_name="Ann")
    second = note(company_id, interview_id, bob, "Agreed", author_name="Bob")
    third = note(company_id, interview_id, ann, "Call them Monday", author_name="Ann")
    again = created(first, "redelivered")

    async def scenario():
        codes = await deliver(again, again, created(second))
        before = await items(cat), await items(ann)
        # Cat opens the bell: the next note starts a new item.
        await notices.mark_seen(cat)
        codes += await deliver(created(third))

        return codes, before, await items(cat), await feed.feed(cat, "en")

    codes, (cat_before, ann_before), cat_after, shown = run(scenario())

    assert codes == [204] * 4
    assert cat_before == [(2, ["Bob", "Ann"], [first["note_id"], second["note_id"]])]
    # Ann's own note isn't in her bell.
    assert ann_before == [(1, ["Bob"], [second["note_id"]])]
    assert cat_after == [(1, ["Ann"], [third["note_id"]]), cat_before[0]]
    assert shown.items[0].link == (f"/companies/{company_id}/interviews/{interview_id}?tab=notes")
    assert shown.unread == 1


def test_a_deleted_note_leaves_the_bell_and_one_deleted_first_never_comes(run, teams):
    company_id, interview_id = company(), str(uuid.uuid4())
    ann, bob = f"ann-{uuid.uuid4()}", f"bob-{uuid.uuid4()}"
    teams[company_id] = [ann, bob]
    kept, gone, late = (note(company_id, interview_id, ann, text) for text in "abc")

    async def scenario():
        await deliver(created(kept), created(gone), deleted(gone), deleted(gone))
        grouped = await items(bob)
        # Deleted before its own event came: nobody hears of it.
        await deliver(deleted(late), created(late))
        await deliver(deleted(kept))

        return grouped, await items(bob)

    grouped, left = run(scenario())

    assert grouped == [(1, [ann.title()], [kept["note_id"]])]
    # The item went with its last note.
    assert left == []


def test_a_deleted_interview_or_company_takes_its_note_items(run, teams):
    company_id, other_company = company(), company()
    interview_id, other_interview = str(uuid.uuid4()), str(uuid.uuid4())
    ann, bob = f"ann-{uuid.uuid4()}", f"bob-{uuid.uuid4()}"
    teams[company_id] = [ann, bob]
    teams[other_company] = [ann, bob]
    interview_gone = {"company_id": company_id, "interview_id": interview_id}

    async def scenario():
        await deliver(
            created(note(company_id, interview_id, ann, "On the deleted interview")),
            created(note(other_company, other_interview, ann, "On the deleted company")),
            ("candidate.interview_deleted", interview_gone, str(uuid.uuid4())),
            ("company.deleted", {"company_id": other_company}, str(uuid.uuid4())),
            # Late events about either tell nobody.
            created(note(company_id, interview_id, ann, "Late")),
            created(note(other_company, other_interview, ann, "Late")),
        )

        return await items(bob)

    assert run(scenario()) == []


def test_a_deleted_account_leaves_its_notes_as_a_former_members(run, teams):
    company_id, interview_id = company(), str(uuid.uuid4())
    ann, bob = f"ann-{uuid.uuid4()}", f"bob-{uuid.uuid4()}"
    teams[company_id] = [ann, bob]
    written = note(company_id, interview_id, ann, "Mine", author_name="Ann")

    async def scenario():
        await deliver(created(written), created(note(company_id, interview_id, bob, "Yours")))
        user_gone = {"user_id": ann, "email": "ann@example.com"}
        await deliver(("user.deleted", user_gone, str(uuid.uuid4())))

        return await items(bob), await items(ann)

    bobs, anns = run(scenario())

    assert bobs == [(1, [None], [written["note_id"]])]
    assert anns == []


def test_a_member_who_left_no_longer_sees_the_companys_note_items(run, teams):
    company_id, interview_id = company(), str(uuid.uuid4())
    ann, bob = f"ann-{uuid.uuid4()}", f"bob-{uuid.uuid4()}"
    teams[company_id] = [ann, bob]

    async def scenario():
        await deliver(created(note(company_id, interview_id, ann, "Before Bob left")))
        member = await feed.feed(bob, "en")
        teams[company_id] = [ann]
        left = await feed.feed(bob, "en", fresh=True)

        return member, left

    member, left = run(scenario())

    assert [(item.kind, member.unread) for item in member.items] == [("note_added", 1)]
    assert (left.items, left.unread) == ([], 0)
