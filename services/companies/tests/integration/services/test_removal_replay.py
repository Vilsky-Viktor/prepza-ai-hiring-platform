"""A candidate a company erased comes back with a restored backup: the daily job (and the step
after a restore) erases them again, and forgets removals past the backups' life."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import insert, select, update

from companies.core.db import Session
from companies.integrations import rounds
from companies.models.invites import CandidateInvite
from companies.models.removals import RemovedInvite
from companies.repositories import interviews, invites
from companies.services import removal_replay
from tests.integration import factories
from tests.integration.transactions import transaction


def test_an_erased_candidate_a_restore_brings_back_is_erased_again(run, monkeypatch):
    sessions_deleted = []

    async def delete_sessions(invite_ids):
        sessions_deleted.extend(invite_ids)

    monkeypatch.setattr(rounds, "delete_invite_sessions", delete_sessions)

    async def scenario():
        company = await factories.company(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        interview = await transaction(interviews.create, company.id, uuid.uuid4(), "en", 60)
        invite, _ = await transaction(
            invites.upsert, interview.id, "gone@example.com", "Backend", "Acme", "en"
        )
        old, _ = await transaction(
            invites.upsert, interview.id, "old@example.com", "Backend", "Acme", "en"
        )
        await transaction(invites.remove, invite, company.id)
        await transaction(invites.remove, old, company.id)

        async with Session() as session:
            # The backup's copy: the invite as it was before the removal.
            await session.execute(
                insert(CandidateInvite).values(
                    {
                        column.key: getattr(invite, column.key)
                        for column in CandidateInvite.__table__.columns
                    }
                )
            )
            # A removal past the backups' life is forgotten, and not replayed.
            await session.execute(
                update(RemovedInvite)
                .where(RemovedInvite.invite_id == old.id)
                .values(removed_at=datetime.now(UTC) - timedelta(days=15))
            )
            await session.commit()

        first = await removal_replay.replay()
        again = await removal_replay.replay()

        async with Session() as session:
            kept = set(await session.scalars(select(RemovedInvite.invite_id)))

        return invite, old, first, again, await transaction(invites.get, invite.id), kept

    invite, old, first, again, found, kept = run(scenario())

    assert (first, again, found) == (1, 0, None)
    assert sessions_deleted == [invite.id]
    assert invite.id in kept and old.id not in kept


def test_a_row_a_deleted_account_once_left_blanked_goes_with_the_daily_job(run, monkeypatch):
    async def nothing(invite_ids):
        pass

    monkeypatch.setattr(rounds, "delete_invite_sessions", nothing)

    async def scenario():
        company = await factories.company(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        interview = await transaction(interviews.create, company.id, uuid.uuid4(), "en", 60)
        blanked, _ = await transaction(
            invites.upsert, interview.id, "x@example.com", "Backend", "Acme", "en"
        )
        kept, _ = await transaction(
            invites.upsert, interview.id, "y@example.com", "Backend", "Acme", "en"
        )

        async with Session() as session:
            await session.execute(
                update(CandidateInvite)
                .where(CandidateInvite.id == blanked.id)
                .values(status="deleted", email=f"deleted-{blanked.id}")
            )
            await session.commit()

        await removal_replay.replay()

        return await transaction(invites.get, blanked.id), await transaction(invites.get, kept.id)

    gone, kept = run(scenario())

    assert gone is None and kept is not None


def test_more_restored_candidates_than_a_batch_are_all_erased_again(run, monkeypatch):
    monkeypatch.setattr(removal_replay, "RETENTION_BATCH", 2)
    monkeypatch.setattr(rounds, "delete_invite_sessions", lambda invite_ids: nothing())

    async def scenario():
        company = await factories.company(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        interview = await transaction(interviews.create, company.id, uuid.uuid4(), "en", 60)
        erased = []

        for number in range(3):
            invite, _ = await transaction(
                invites.upsert,
                interview.id,
                f"c{number}-{uuid.uuid4()}@example.com",
                "Backend",
                "Acme",
                "en",
            )
            await transaction(invites.remove, invite, company.id)
            erased.append(invite)

        async with Session() as session:
            # The backup's copies: the invites as they were before their removal.
            for invite in erased:
                await session.execute(
                    insert(CandidateInvite).values(
                        {
                            column.key: getattr(invite, column.key)
                            for column in CandidateInvite.__table__.columns
                        }
                    )
                )

            await session.commit()

        count = await removal_replay.replay()
        found = [await transaction(invites.get, invite.id) for invite in erased]
        await factories.deleted(company.id)

        return count, found

    count, found = run(scenario())

    assert count == 3
    assert found == [None, None, None]


async def nothing():
    pass
