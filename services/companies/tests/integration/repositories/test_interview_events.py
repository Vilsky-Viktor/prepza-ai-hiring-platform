"""The events ats consumes are saved with their change, in the same transaction, once."""

import uuid

from sqlalchemy import select

from companies.core.db import Session
from companies.models.outbox import OutboxEvent
from companies.repositories import (
    interview_generations,
    interviews,
    invite_progress,
    invites,
)
from tests.integration import factories
from tests.integration.transactions import transaction


async def interview():
    company = await factories.company(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")

    return await transaction(interviews.create, company.id, uuid.uuid4(), "en", 60)


async def events(event_type: str, key: str, value: str) -> list[dict]:
    """The data of the outbox's events of that type whose `key` is `value`."""
    async with Session() as session:
        return list(
            await session.scalars(
                select(OutboxEvent.data).where(
                    OutboxEvent.event_type == event_type, OutboxEvent.data[key].astext == value
                )
            )
        )


def test_a_finished_candidate_delivered_twice_is_announced_once(run):
    async def scenario():
        found = await interview()
        invite, _ = await transaction(
            invites.upsert, found.id, "gus@example.com", "Backend", "Acme", "en"
        )
        result = {"candidate_invite_id": str(invite.id), "grade": 70, "passed": True}
        event_id = str(uuid.uuid4())
        await transaction(invite_progress.finish, invite.id, 70, False, None, event_id, result)
        await transaction(invite_progress.finish, invite.id, 70, False, None, event_id, result)

        return result, await events("candidate.finished", "candidate_invite_id", str(invite.id))

    result, saved = run(scenario())

    assert saved == [result]


def test_an_interview_made_ready_twice_by_one_event_is_announced_once(run):
    async def scenario():
        found = await interview()
        event_id = str(uuid.uuid4())

        for _ in range(2):
            await transaction(
                interview_generations.set_generated,
                found.generation_id,
                uuid.uuid4(),
                "Backend",
                None,
                {"kind": "x"},
                event_id,
            )

        return found, await events("interview.ready", "interview_id", str(found.id))

    found, saved = run(scenario())

    assert saved == [{"interview_id": str(found.id), "company_id": str(found.company_id)}]


def test_a_removed_interview_is_announced_once(run):
    async def scenario():
        found = await interview()
        await factories.interview_removed(found.id)
        await factories.interview_removed(found.id)

        return found, await events("interview.deleted", "interview_id", str(found.id))

    found, saved = run(scenario())

    assert saved == [{"interview_id": str(found.id), "company_id": str(found.company_id)}]


def test_a_cancelled_generations_interview_is_announced_as_deleted(run):
    async def scenario():
        found = await interview()
        await transaction(
            interview_generations.remove_for_generation, found.generation_id, {"kind": "x"}
        )
        await transaction(
            interview_generations.remove_for_generation, found.generation_id, {"kind": "x"}
        )

        return found, await events("interview.deleted", "interview_id", str(found.id))

    found, saved = run(scenario())

    assert saved == [{"interview_id": str(found.id), "company_id": str(found.company_id)}]


def test_interviews_by_ids_skip_the_ones_gone(run):
    async def scenario():
        kept, gone = await interview(), await interview()
        await factories.interview_removed(gone.id)
        found = await transaction(interviews.by_ids, [kept.id, gone.id, uuid.uuid4()])

        return kept, [item.id for item in found], await transaction(interviews.by_ids, [])

    kept, found, none = run(scenario())

    assert (found, none) == ([kept.id], [])


def test_a_failed_generation_marks_its_interview_once_until_the_questions_come(run):
    async def scenario():
        found = await interview()
        event_id = str(uuid.uuid4())
        await transaction(interview_generations.mark_failed, found.generation_id, event_id)
        failed = (await transaction(interviews.get, found.id)).generation_failed
        # Retried; the same event delivered again doesn't mark it again.
        await transaction(interview_generations.set_generation_failed, found.id, False)
        await transaction(interview_generations.mark_failed, found.generation_id, event_id)
        redelivered = (await transaction(interviews.get, found.id)).generation_failed
        # Failed again, then the retry's questions come: they clear it, and a late failure of
        # an earlier run leaves the ready interview alone.
        await transaction(interview_generations.mark_failed, found.generation_id, str(uuid.uuid4()))
        await transaction(
            interview_generations.set_generated,
            found.generation_id,
            uuid.uuid4(),
            "Backend",
            None,
            {"kind": "x"},
            str(uuid.uuid4()),
        )
        await transaction(interview_generations.mark_failed, found.generation_id, str(uuid.uuid4()))

        return failed, redelivered, await transaction(interviews.get, found.id)

    failed, redelivered, ready = run(scenario())

    assert (failed, redelivered) == (True, False)
    assert ready.generation_failed is False and ready.set_id is not None


def test_a_removed_interview_returns_its_unfinished_invites_for_their_credits(run):
    async def scenario():
        found = await interview()
        waiting, _ = await transaction(
            invites.upsert, found.id, "w@example.com", "Backend", "Acme", "en"
        )
        done, _ = await transaction(
            invites.upsert, found.id, "d@example.com", "Backend", "Acme", "en"
        )
        await transaction(invite_progress.finish, done.id, 80, False, None)

        return (
            waiting,
            await factories.interview_removed(found.id),
            await factories.interview_removed(found.id),
        )

    waiting, removed, again = run(scenario())

    # A finished candidate stays charged, so only the waiting one is returned.
    assert removed == [(waiting.interview_id, "w@example.com", "invited", waiting.hold_key)]
    assert again == []


def test_a_removed_invite_says_its_status_as_it_was_deleted(run):
    async def scenario():
        found = await interview()
        invite, _ = await transaction(
            invites.upsert, found.id, "s@example.com", "Backend", "Acme", "en"
        )
        await transaction(invite_progress.start, invite.id, "s-uid")

        return await transaction(invites.remove, invite, found.company_id), await transaction(
            invites.remove, invite, found.company_id
        )

    # Started since it was read: revoking it erases the sessions that start made.
    assert run(scenario()) == ("in_process", None)


def test_a_deleted_interview_tells_the_services_that_keep_its_candidates(run):
    async def scenario():
        found = await interview()
        await factories.interview_removed(found.id)

        return found, await events("candidate.interview_deleted", "interview_id", str(found.id))

    found, saved = run(scenario())

    assert saved == [{"interview_id": str(found.id), "company_id": str(found.company_id)}]
