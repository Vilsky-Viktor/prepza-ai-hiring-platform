"""A candidate's invite started twice at once (two tabs, a double click), or started while the
company sends it again, proven to overlap: the first call's transaction stays open at its commit
until the second is seen waiting on the invite's row lock (prepza_common.lock_waits)."""

import os
import uuid
from datetime import UTC, datetime, timedelta

from prepza_common.lock_waits import hold_first_commit, race
from sqlalchemy import select

from app.constants.events import CANDIDATE_STARTED
from app.constants.invites import InviteStatus
from app.models.outbox import OutboxEvent
from app.storage import companies, interviews, invite_expiry, invite_progress, invites
from app.storage.db import Session


def test_two_starts_at_once_start_the_invite_once(run, monkeypatch):
    async def scenario():
        company = await companies.create(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        interview = await interviews.create(company.id, uuid.uuid4(), "en", 60)
        invite, _ = await invites.upsert(interview.id, "s@example.com", "B", "A", "en")
        held = hold_first_commit(monkeypatch, invite_progress)
        before = await race(
            os.environ["DATABASE_URL"],
            held,
            invite_progress.start(invite.id, "uid-1"),
            invite_progress.start(invite.id, "uid-1"),
        )

        async with Session() as session:
            started = await session.scalars(
                select(OutboxEvent).where(
                    OutboxEvent.event_type == CANDIDATE_STARTED,
                    OutboxEvent.data["candidate_invite_id"].astext == str(invite.id),
                )
            )

            return before, len(started.all())

    before, started = run(scenario())

    assert before == (InviteStatus.INVITED, InviteStatus.IN_PROCESS)
    assert started == 1


def test_sending_an_expired_invite_again_while_its_candidate_starts_keeps_the_start(
    run, monkeypatch
):
    async def scenario():
        company = await companies.create(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        interview = await interviews.create(company.id, uuid.uuid4(), "en", 60)
        invite, _ = await invites.upsert(interview.id, "s@example.com", "B", "A", "en", name="Ann")
        await invite_expiry.mark_expired(invite.id, datetime.now(UTC) + timedelta(seconds=1))
        held = hold_first_commit(monkeypatch, invite_progress)
        _, (_, revived) = await race(
            os.environ["DATABASE_URL"],
            held,
            invite_progress.start(invite.id, "uid-1"),
            invites.upsert(interview.id, "s@example.com", "B", "A", "en", name="Ann"),
        )

        return revived, (await invites.get(invite.id)).status

    assert run(scenario()) == (False, InviteStatus.IN_PROCESS)
