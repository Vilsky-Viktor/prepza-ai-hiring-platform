"""What notifications reads for its digest and reminders: members, and interviews waiting."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import update

from companies.core.db import Session
from companies.models.interviews import Interview
from companies.repositories import (
    companies,
    email_reminders,
    interview_generations,
    interviews,
    invites,
)


async def company():
    return await companies.create(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")


async def ready_at(interview_id, when):
    async with Session() as session:
        await session.execute(
            update(Interview).where(Interview.id == interview_id).values(ready_at=when)
        )
        await session.commit()


def test_an_interview_is_ready_when_it_gets_its_questions_once(run):
    async def scenario():
        found = await company()
        generated = await interviews.create(found.id, uuid.uuid4(), "en", 60)
        before = (await interviews.get(generated.id)).ready_at
        await interview_generations.set_generated(
            generated.generation_id, uuid.uuid4(), "Backend", None, {}, str(uuid.uuid4())
        )
        first = (await interviews.get(generated.id)).ready_at
        # Regenerated questions don't move it.
        await interview_generations.set_generated(
            generated.generation_id, uuid.uuid4(), "Backend", None, {}, str(uuid.uuid4())
        )
        second = (await interviews.get(generated.id)).ready_at
        template = await interviews.create_from_template(found.id, uuid.uuid4(), "Design", "en", 60)

        return before, first, second, (await interviews.get(template.id)).ready_at

    before, first, second, template = run(scenario())

    assert before is None
    assert first is not None and second == first
    assert template is not None


def test_waiting_interviews_are_ready_ones_nobody_was_invited_to_and_ones_still_generating(run):
    now = datetime.now(UTC)

    async def scenario():
        found = await company()
        idle = await interviews.create_from_template(found.id, uuid.uuid4(), "Idle", "en", 60)
        invited = await interviews.create_from_template(found.id, uuid.uuid4(), "Invited", "en", 60)
        recent = await interviews.create_from_template(found.id, uuid.uuid4(), "Recent", "en", 60)
        hired = await interviews.create_from_template(found.id, uuid.uuid4(), "Hired", "en", 60)
        generating = await interviews.create(found.id, uuid.uuid4(), "en", 60)
        await invites.upsert(invited.id, "gus@example.com", "Invited", "Acme", "en")

        for interview in (idle, invited, hired):
            await ready_at(interview.id, now - timedelta(days=4))

        async with Session() as session:
            await session.execute(
                update(Interview).where(Interview.id == hired.id).values(hired=True)
            )
            await session.commit()

        windows = (
            (now - timedelta(days=10), now - timedelta(days=3)),
            (now - timedelta(days=15), now + timedelta(minutes=1)),
        )
        without, being = await email_reminders.waiting_of(*windows, [found.id, uuid.uuid4()])
        ids = {idle.id, invited.id, recent.id, hired.id, generating.id}

        return (
            {row.id for row in without} & ids,
            {row.id for row in being} & ids,
            idle.id,
            generating.id,
        )

    without, being, idle, generating = run(scenario())

    assert without == {idle}
    assert being == {generating}


def test_companies_with_waiting_interviews_come_in_order_a_page_at_a_time(run):
    now = datetime.now(UTC)
    windows = (
        (now - timedelta(days=10), now - timedelta(days=3)),
        (now - timedelta(days=15), now + timedelta(minutes=1)),
    )

    async def scenario():
        idle, generating, quiet = await company(), await company(), await company()
        waiting = await interviews.create_from_template(idle.id, uuid.uuid4(), "Idle", "en", 60)
        await ready_at(waiting.id, now - timedelta(days=4))
        await interviews.create(generating.id, uuid.uuid4(), "en", 60)
        await interviews.create_from_template(quiet.id, uuid.uuid4(), "Recent", "en", 60)
        mine = sorted([idle.id, generating.id, quiet.id])
        # Two companies a page, from just before this test's first company until past its last.
        pages, after = [], uuid.UUID(int=mine[0].int - 1)

        while True:
            page = await email_reminders.waiting_company_ids(*windows, after, 2)
            pages.append(page)

            if len(page) < 2 or page[-1] >= mine[-1]:
                break

            after = page[-1]

        found = [company_id for page in pages for company_id in page]

        return [company_id for company_id in found if company_id in mine], found, idle, generating

    mine, found, idle, generating = run(scenario())

    assert mine == sorted([idle.id, generating.id])
    # In order, each once, every page going on after the last.
    assert found == sorted(set(found))


def test_members_come_with_their_company_and_whether_they_can_act(run):
    async def scenario():
        found = await company()

        return found.id, await email_reminders.with_members([found.id, uuid.uuid4()])

    company_id, found = run(scenario())

    [only] = found
    assert only.id == company_id
    assert [(member.user_id, member.role) for member in only.members] == [("owner", "owner")]
