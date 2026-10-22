from datetime import UTC, datetime, timedelta

from sqlalchemy import update

from app.constants.invites import InviteStatus
from app.helpers.notifications import invite_undelivered
from app.models.invites import CandidateInvite
from app.storage import candidate_updates, invite_progress, invites
from app.storage.db import Session
from tests.integration.test_invites import interview

SINCE = datetime(2026, 10, 1, 9, tzinfo=UTC)
UNTIL = datetime(2026, 10, 1, 17, tzinfo=UTC)


async def invited(found, email, **values):
    """An invite of `found` with these columns set as given."""
    invite, _ = await invites.upsert(found.id, email, "Backend", "Acme", "en")

    async with Session() as session:
        await session.execute(
            update(CandidateInvite).where(CandidateInvite.id == invite.id).values(**values)
        )
        await session.commit()

    return invite


def test_changed_finds_the_company_invites_with_a_step_in_the_window(run):
    inside = SINCE + timedelta(hours=1)

    async def scenario():
        found, other = await interview(), await interview()
        expected = [
            await invited(found, "ann@example.com", started_at=inside),
            await invited(found, "bob@example.com", finished_at=UNTIL),
            await invited(found, "cid@example.com", undelivered_at=inside),
        ]
        await invited(found, "dan@example.com", started_at=SINCE)
        await invited(found, "eve@example.com", finished_at=UNTIL + timedelta(seconds=1))
        await invited(found, "fay@example.com", started_at=inside, status=InviteStatus.DELETED)
        await invited(other, "gil@example.com", started_at=inside)
        rows = await candidate_updates.changed([found.company_id], SINCE, UNTIL, 50)

        return rows, expected, found

    rows, expected, found = run(scenario())

    assert sorted(invite.id for invite, _ in rows) == sorted(invite.id for invite in expected)
    assert {interview_row.id for _, interview_row in rows} == {found.id}


def test_only_the_newest_are_listed_and_every_one_is_counted(run):
    async def scenario():
        found = await interview()

        async with Session() as session:
            await session.execute(
                update(type(found)).where(type(found).id == found.id).values(pass_mark=50)
            )
            await session.commit()

        for minute, grade in ((10, 80), (20, 30), (30, 90)):
            await invited(
                found,
                f"c{minute}@example.com",
                started_at=SINCE + timedelta(minutes=minute),
                finished_at=SINCE + timedelta(minutes=minute + 1),
                grade=grade,
            )

        await invited(found, "late@example.com", undelivered_at=SINCE + timedelta(minutes=40))
        newest = await candidate_updates.changed([found.company_id], SINCE, UNTIL, 2)
        counts = await candidate_updates.counts([found.company_id], SINCE, UNTIL)

        return [invite.email for invite, _ in newest], counts

    newest, counts = run(scenario())

    assert newest == ["late@example.com", "c30@example.com"]
    # Started, finished, passed (80 and 90 of a pass mark of 50), undelivered.
    assert counts == (3, 3, 2, 1)


def test_marking_an_invite_undelivered_records_when(run):
    async def scenario():
        found = await interview()
        invite, _ = await invites.upsert(found.id, "hal@example.com", "Backend", "Acme", "en")
        before = datetime.now(UTC)
        await invite_progress.mark_undelivered(
            invite.id, invite_undelivered(found, str(invite.id), invite.email)
        )

        return before, await invites.get(invite.id)

    before, marked = run(scenario())

    assert marked.undelivered_at >= before - timedelta(seconds=5)
