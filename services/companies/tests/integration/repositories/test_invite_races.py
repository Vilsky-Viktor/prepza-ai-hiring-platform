"""A candidate's invite started twice at once (two tabs, a double click), or started while the
company sends it again, proven to overlap: the first call's transaction stays open at its commit
until the second is seen waiting on the invite's row lock (prepza_common.db.lock_waits)."""

import os
import uuid
from datetime import UTC, datetime, timedelta

from prepza_common.db.lock_waits import hold_first_commit, race
from sqlalchemy import select

from companies.constants.events import CANDIDATE_STARTED
from companies.constants.invites import InviteStatus
from companies.core.db import Session
from companies.models.outbox import OutboxEvent
from companies.repositories import interviews, invite_expiry, invite_progress, invites
from tests.integration import factories, transactions
from tests.integration.transactions import transaction


def test_two_starts_at_once_start_the_invite_once(run, monkeypatch):
    async def scenario():
        company = await factories.company(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        interview = await transaction(interviews.create, company.id, uuid.uuid4(), "en", 60)
        invite, _ = await transaction(invites.upsert, interview.id, "s@example.com", "B", "A", "en")
        held = hold_first_commit(monkeypatch, transactions)
        before = await race(
            os.environ["DATABASE_URL"],
            held,
            transaction(invite_progress.start, invite.id, "uid-1"),
            transaction(invite_progress.start, invite.id, "uid-1"),
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
        company = await factories.company(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        interview = await transaction(interviews.create, company.id, uuid.uuid4(), "en", 60)
        invite, _ = await transaction(
            invites.upsert, interview.id, "s@example.com", "B", "A", "en", name="Ann"
        )
        await transaction(
            invite_expiry.mark_expired, invite.id, datetime.now(UTC) + timedelta(seconds=1)
        )
        held = hold_first_commit(monkeypatch, transactions)
        _, (_, revived) = await race(
            os.environ["DATABASE_URL"],
            held,
            transaction(invite_progress.start, invite.id, "uid-1"),
            transaction(invites.upsert, interview.id, "s@example.com", "B", "A", "en", name="Ann"),
        )

        return revived, (await transaction(invites.get, invite.id)).status

    assert run(scenario()) == (False, InviteStatus.IN_PROCESS)
