import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from companies.constants.invites import InviteStatus
from companies.core.db import Session
from companies.helpers.notifications import invite_undelivered
from companies.models.outbox import OutboxEvent
from companies.repositories import (
    companies,
    interviews,
    invite_progress,
    invites,
    reminders,
)
from tests.integration import factories
from tests.integration.transactions import transaction


async def interview():
    company = await factories.company(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")

    return await transaction(interviews.create, company.id, uuid.uuid4(), "en", 60)


def test_inviting_the_same_address_again_returns_the_same_invite(run):
    async def scenario():
        found = await interview()
        first, _ = await transaction(
            invites.upsert, found.id, "Carol@Example.com", "Backend", "Acme", "en"
        )
        again, _ = await transaction(
            invites.upsert, found.id, "carol@example.com", "Backend", "Acme", "en"
        )

        return first, again

    first, again = run(scenario())

    assert (first.id, first.token) == (again.id, again.token)
    assert first.email == "carol@example.com"
    assert first.status == InviteStatus.INVITED


def test_an_undelivered_invite_is_marked_until_it_is_sent_again(run):
    async def scenario():
        found = await interview()
        invite, _ = await transaction(
            invites.upsert, found.id, "erin@example.com", "Backend", "Acme", "en"
        )
        await transaction(
            invite_progress.mark_undelivered,
            invite.id,
            invite_undelivered(found, str(invite.id), invite.email),
        )
        bounced, _ = await transaction(invites.get_by_token, invite.token)
        await transaction(invites.upsert, found.id, "erin@example.com", "Backend", "Acme", "en")
        resent, _ = await transaction(invites.get_by_token, invite.token)

        return bounced, resent

    bounced, resent = run(scenario())

    assert bounced.status == InviteStatus.UNDELIVERED
    assert resent.status == InviteStatus.INVITED


def test_a_started_invite_is_never_marked_undelivered(run):
    async def scenario():
        found = await interview()
        invite, _ = await transaction(
            invites.upsert, found.id, "fay@example.com", "Backend", "Acme", "en"
        )
        await transaction(invite_progress.start, invite.id, "fay-uid")
        await transaction(
            invite_progress.mark_undelivered,
            invite.id,
            invite_undelivered(found, str(invite.id), invite.email),
        )
        stored, _ = await transaction(invites.get_by_token, invite.token)

        return stored

    assert run(scenario()).status == InviteStatus.IN_PROCESS


def test_an_invite_moves_from_invited_to_in_process_to_finished(run):
    async def scenario():
        found = await interview()
        invite, _ = await transaction(
            invites.upsert, found.id, "dave@example.com", "Backend", "Acme", "en"
        )
        await transaction(invite_progress.start, invite.id, "dave-uid")
        started, _ = await transaction(invites.get_by_token, invite.token)
        await transaction(invite_progress.finish, invite.id, 80, False, None)
        # Starting again, e.g. reopening the link, never reopens a finished interview.
        await transaction(invite_progress.start, invite.id, "dave-uid")
        finished, _ = await transaction(invites.get_by_token, invite.token)

        return started, finished

    started, finished = run(scenario())

    assert (started.status, started.user_id) == (InviteStatus.IN_PROCESS, "dave-uid")
    assert (finished.status, finished.grade, finished.flagged) == (InviteStatus.FINISHED, 80, False)


def test_only_interviews_without_a_candidate_count_as_waiting(run):
    async def scenario():
        company = await factories.company(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        first = await transaction(interviews.create, company.id, uuid.uuid4(), "en", 60)
        await transaction(interviews.create, company.id, uuid.uuid4(), "en", 60)
        await transaction(
            interviews.create_from_template, company.id, uuid.uuid4(), "Copied", "en", 60
        )
        before = await transaction(interviews.without_candidates, company.id)
        invite, _ = await transaction(
            invites.upsert, first.id, "dan@example.com", "Backend", "Acme", "en"
        )
        invited = await transaction(interviews.without_candidates, company.id)
        await transaction(invites.remove, invite, company.id)
        revoked = await transaction(interviews.without_candidates, company.id)

        return before, invited, revoked

    # Two generated waiting (a template's copy costs nothing and doesn't count); an invite takes
    # one out; revoking the invite puts it back.
    assert run(scenario()) == (2, 1, 2)


def test_a_candidate_who_has_not_started_is_reminded_once_until_invited_again(run):
    async def scenario():
        found = await interview()
        await transaction(interviews.set_title, found.id, "Backend")
        invite, _ = await transaction(
            invites.upsert, found.id, "rita@example.com", "Backend", "Acme", "en"
        )
        later = datetime.now(UTC) + timedelta(seconds=1)
        first = await transaction(reminders.remind_unstarted, later)
        again = await transaction(reminders.remind_unstarted, later)
        await transaction(invites.upsert, found.id, "rita@example.com", "Backend", "Acme", "en")
        after_resend = await transaction(
            reminders.remind_unstarted, datetime.now(UTC) + timedelta(seconds=1)
        )

        async with Session() as session:
            sent = list(
                await session.scalars(
                    select(OutboxEvent.data).where(
                        OutboxEvent.event_type == "candidate.reminded",
                        OutboxEvent.data["invite_id"].astext == str(invite.id),
                    )
                )
            )

        return found, first, again, after_resend, sent

    found, first, again, after_resend, sent = run(scenario())

    # Other tests' invites may be reminded too: at least this one, then none, then this one.
    assert first >= 1
    assert again == 0
    assert after_resend == 1
    # Each names the company, so notifications skips an address that stopped its emails.
    assert [event["company_id"] for event in sent] == [str(found.company_id)] * 2


def test_a_finished_interview_delivered_twice_notifies_the_company_once(run):
    async def scenario():
        found = await interview()
        invite, _ = await transaction(
            invites.upsert, found.id, "gus@example.com", "Backend", "Acme", "en"
        )
        notice = {"kind": "candidate_finished", "invite": str(invite.id)}
        event_id = str(uuid.uuid4())
        await transaction(invite_progress.finish, invite.id, 70, False, notice, event_id)
        await transaction(invite_progress.finish, invite.id, 70, False, notice, event_id)

        async with Session() as session:
            return await session.scalar(
                select(func.count())
                .select_from(OutboxEvent)
                .where(OutboxEvent.data["invite"].astext == str(invite.id))
            )

    assert run(scenario()) == 1


def test_a_candidate_invited_again_after_removal_is_held_under_a_new_key(run, monkeypatch):
    # A finished candidate removed and invited again must be charged again: billing keeps a
    # charged key charged, so the new invite needs its own key.
    from testee_common.auth.user import User

    from companies.integrations import billing
    from companies.repositories import interview_generations
    from companies.services import candidate_invites

    held = []

    async def hold(company_id, key):
        held.append(key)

    monkeypatch.setattr(billing, "hold_candidate", hold)
    owner = User(uid="owner", email="owner@example.com", email_verified=True)

    async def scenario():
        found = await interview()
        await transaction(interviews.set_title, found.id, "Backend")
        await transaction(interview_generations.set_set_id, found.id, uuid.uuid4())
        found = await transaction(interviews.get, found.id)
        company = await transaction(companies.get, found.company_id)
        first = await candidate_invites.invite(found, company, owner, "dana@example.com")
        resent = await candidate_invites.invite(found, company, owner, "dana@example.com")
        await transaction(invites.remove, first, found.company_id)
        again = await candidate_invites.invite(found, company, owner, "dana@example.com")

        return first, resent, again, await transaction(invites.held, found.id, "dana@example.com")

    first, resent, again, (status, stored) = run(scenario())

    assert first.hold_key and first.hold_key == resent.hold_key
    assert again.hold_key != first.hold_key
    # The resend holds the same key again (billing does it once); the new invite a new one.
    assert held == [first.hold_key, first.hold_key, again.hold_key]
    assert (status, stored) == (InviteStatus.INVITED, again.hold_key)


def test_removing_a_candidate_tells_the_other_services_to_forget_them(run):
    async def scenario():
        found = await interview()
        invite, _ = await transaction(
            invites.upsert, found.id, "hal@example.com", "Backend", "Acme", "en"
        )
        await transaction(invites.remove, invite, found.company_id)

        async with Session() as session:
            events = (
                await session.scalars(
                    select(OutboxEvent.data).where(
                        OutboxEvent.event_type == "candidate.removed",
                        OutboxEvent.data["interview_id"].astext == str(found.id),
                    )
                )
            ).all()

        return found, await transaction(invites.status_of, found.id, "hal@example.com"), events

    found, status, events = run(scenario())

    assert status is None
    assert events == [
        {
            "company_id": str(found.company_id),
            "interview_id": str(found.id),
            "email": "hal@example.com",
            "candidate_invite_id": events[0]["candidate_invite_id"],
        }
    ]
