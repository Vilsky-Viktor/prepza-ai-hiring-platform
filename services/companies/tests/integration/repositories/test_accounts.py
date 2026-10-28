import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from companies.constants.invites import NOT_STARTED, InviteStatus
from companies.core.db import Session
from companies.models.outbox import OutboxEvent
from companies.repositories import (
    accounts,
    candidates,
    companies,
    interviews,
    invite_progress,
    invites,
)
from companies.services import accounts as account_service
from tests.integration import factories
from tests.integration.transactions import transaction


def test_a_deleted_candidates_invites_go_and_the_other_services_are_told(run):
    async def scenario():
        company = await factories.company(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        interview = await transaction(interviews.create, company.id, uuid.uuid4(), "en", 60)
        first, _ = await transaction(
            invites.upsert, interview.id, "gone@example.com", "Backend", "Acme", "en"
        )
        await transaction(invite_progress.start, first.id, "gone")
        # A second address of the same person, never started: matched by email.
        await transaction(
            invites.upsert, interview.id, "Gone2@Example.com", "Backend", "Acme", "en"
        )
        await transaction(
            invites.upsert, interview.id, "stays@example.com", "Backend", "Acme", "en"
        )
        await account_service.forget("gone", "gone2@example.com", [])

        async with Session() as session:
            told = list(
                await session.scalars(
                    select(OutboxEvent.data["candidate_invite_id"].astext).where(
                        OutboxEvent.event_type == "candidate.removed",
                        OutboxEvent.data["interview_id"].astext == str(interview.id),
                    )
                )
            )

        return first, await transaction(candidates.page, interview.id, 0, 10, False), told

    first, rows, told = run(scenario())

    # Nothing of theirs is left, not even a row without their email: its times and grade would
    # still point to them.
    assert [row.email for row in rows] == ["stays@example.com"]
    assert str(first.id) in told and len(told) == 2


def test_memberships_report_how_many_owners_each_company_has(run):
    async def scenario():
        alone = await factories.company("Alone Inc", "ann", "ann@example.com")
        found = await transaction(accounts.memberships, "ann")

        return alone.id, found

    company_id, found = run(scenario())

    assert [(company.id, owners) for _, company, owners in found] == [(company_id, 1)]


def test_only_invites_older_than_the_cutoff_expire(run):
    async def scenario():
        company = await factories.company(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        interview = await transaction(interviews.create, company.id, uuid.uuid4(), "en", 60)
        invite, _ = await transaction(
            invites.upsert, interview.id, "carol@example.com", "Backend", "Acme", "en"
        )
        recent = await transaction(
            accounts.expired_invites, datetime.now(UTC) - timedelta(days=365), 1000
        )
        everything = await transaction(
            accounts.expired_invites, datetime.now(UTC) + timedelta(seconds=1), 1000
        )
        await transaction(accounts.delete_invites, [invite.id])

        return invite.id, recent, everything, await transaction(invites.get_by_token, invite.token)

    invite_id, recent, everything, after = run(scenario())

    assert invite_id not in [row[0] for row in recent]
    assert (invite_id, "carol@example.com", InviteStatus.INVITED) in [
        (row[0], row[2], row[3]) for row in everything
    ]
    assert after is None


def test_a_deleted_accounts_verification_email_goes_and_is_in_its_data_until_then(run):
    from companies.repositories import verification

    async def scenario():
        company = await factories.company(f"Acme {uuid.uuid4()}", "ann", "ann@example.com")
        email = f"Ann-{uuid.uuid4().hex[:8]}@Acme.com"
        await transaction(verification.set_website, company.id, "acme.com", email)
        exported = await transaction(accounts.export, "ann", email.lower())
        await transaction(accounts.forget_verification_email, email.lower())
        after = await transaction(companies.get, company.id)

        return company.name, email, exported["company_verifications"], after

    name, email, exported, after = run(scenario())

    assert exported == [{"company": name, "verification_email": email}]
    assert after.verification_email is None
    assert after.website_domain == "acme.com"


def test_a_candidates_data_includes_when_they_pledged_to_answer_on_their_own(run):
    async def scenario():
        company = await factories.company(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        interview = await transaction(interviews.create, company.id, uuid.uuid4(), "en", 60)
        email = f"pledge-{uuid.uuid4().hex[:8]}@example.com"
        invite, _ = await transaction(invites.upsert, interview.id, email, "Backend", "Acme", "en")
        await transaction(invite_progress.start, invite.id, f"u-{invite.id}")
        exported = await transaction(accounts.export, f"u-{invite.id}", email)

        return await transaction(invites.get, invite.id), exported["interview_invites"]

    stored, exported = run(scenario())

    assert [row["pledged_at"] for row in exported] == [stored.pledged_at]
    assert stored.pledged_at is not None


def test_a_deleted_accounts_pending_team_invites_go_and_are_in_its_data_until_then(run):
    from companies.repositories import members

    async def scenario():
        company = await factories.company(f"Acme {uuid.uuid4()}", "ann", "ann@example.com")
        email = f"bo-{uuid.uuid4().hex[:8]}@example.com"
        other = f"cy-{uuid.uuid4().hex[:8]}@example.com"
        sender = {"company": company.name, "inviter": "ann@example.com", "language": "en"}
        await factories.member(company.id, email.upper(), "admin", sender)
        await factories.member(company.id, other, "viewer", sender)
        exported = await transaction(accounts.export, "bo", email)
        # An unverified account's email is empty: it matches no one.
        await transaction(accounts.forget_member_invites, "")
        await transaction(accounts.forget_member_invites, email)
        left = await transaction(members.list_for_company, company.id, 0, 10)

        return company.name, exported["company_invitations"], left, other

    name, exported, left, other = run(scenario())

    assert [(row["company"], row["role"]) for row in exported] == [(name, "admin")]
    assert {row.invited_email for row in left if row.user_id is None} == {other}


def test_a_candidates_data_includes_their_extra_time_and_when_they_started(run):
    async def scenario():
        company = await factories.company(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        interview = await transaction(interviews.create, company.id, uuid.uuid4(), "en", 60)
        email = f"time-{uuid.uuid4().hex[:8]}@example.com"
        invite, _ = await transaction(invites.upsert, interview.id, email, "Backend", "Acme", "en")
        await transaction(invites.change, invite.id, {"extra_time": 30}, NOT_STARTED)
        await transaction(invite_progress.start, invite.id, f"u-{invite.id}")
        [row] = (await transaction(accounts.export, f"u-{invite.id}", email))["interview_invites"]

        return await transaction(invites.get, invite.id), row

    stored, row = run(scenario())

    assert (row["extra_time"], row["started_at"]) == (30, stored.started_at)
    assert row["started_at"] is not None and row["finished_at"] is None
