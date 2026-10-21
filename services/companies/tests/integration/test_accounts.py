import uuid
from datetime import UTC, datetime, timedelta

from app.constants.invites import InviteStatus
from app.storage import accounts, candidates, companies, interviews, invite_progress, invites


def test_a_deleted_candidate_keeps_a_row_without_their_email(run):
    async def scenario():
        company = await companies.create(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        interview = await interviews.create(company.id, uuid.uuid4(), "en", 60)
        first, _ = await invites.upsert(interview.id, "gone@example.com", "Backend", "Acme", "en")
        await invite_progress.start(first.id, "gone")
        # A second address of the same person, never started: matched by email.
        await invites.upsert(interview.id, "Gone2@Example.com", "Backend", "Acme", "en")
        await accounts.forget_candidate("gone", "gone2@example.com")

        return (
            await candidates.page(interview.id, 0, 10, False),
            await invites.get_by_token(first.token),
        )

    rows, by_old_token = run(scenario())

    assert {row.status for row in rows} == {InviteStatus.DELETED}
    assert all(row.email.startswith("deleted-") and row.user_id is None for row in rows)
    assert by_old_token is None


def test_memberships_report_how_many_owners_each_company_has(run):
    async def scenario():
        alone = await companies.create("Alone Inc", "ann", "ann@example.com")
        found = await accounts.memberships("ann")

        return alone.id, found

    company_id, found = run(scenario())

    assert [(company.id, owners) for _, company, owners in found] == [(company_id, 1)]


def test_only_invites_older_than_the_cutoff_expire(run):
    async def scenario():
        company = await companies.create(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        interview = await interviews.create(company.id, uuid.uuid4(), "en", 60)
        invite, _ = await invites.upsert(interview.id, "carol@example.com", "Backend", "Acme", "en")
        recent = await accounts.expired_invites(datetime.now(UTC) - timedelta(days=365), 1000)
        everything = await accounts.expired_invites(datetime.now(UTC) + timedelta(seconds=1), 1000)
        await accounts.delete_invites([invite.id])

        return invite.id, recent, everything, await invites.get_by_token(invite.token)

    invite_id, recent, everything, after = run(scenario())

    assert invite_id not in [row[0] for row in recent]
    assert (invite_id, "carol@example.com", InviteStatus.INVITED) in [
        (row[0], row[2], row[3]) for row in everything
    ]
    assert after is None


def test_a_deleted_accounts_verification_email_goes_and_is_in_its_data_until_then(run):
    from app.storage import verification

    async def scenario():
        company = await companies.create(f"Acme {uuid.uuid4()}", "ann", "ann@example.com")
        email = f"Ann-{uuid.uuid4().hex[:8]}@Acme.com"
        await verification.set_website(company.id, "acme.com", email)
        exported = await accounts.export("ann", email.lower())
        await accounts.forget_verification_email(email.lower())
        after = await companies.get(company.id)

        return company.name, email, exported["company_verifications"], after

    name, email, exported, after = run(scenario())

    assert exported == [{"company": name, "verification_email": email}]
    assert after.verification_email is None
    assert after.website_domain == "acme.com"


def test_a_candidates_data_includes_when_they_pledged_to_answer_on_their_own(run):
    async def scenario():
        company = await companies.create(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        interview = await interviews.create(company.id, uuid.uuid4(), "en", 60)
        email = f"pledge-{uuid.uuid4().hex[:8]}@example.com"
        invite, _ = await invites.upsert(interview.id, email, "Backend", "Acme", "en")
        await invite_progress.start(invite.id, f"u-{invite.id}")
        exported = await accounts.export(f"u-{invite.id}", email)

        return await invites.get(invite.id), exported["interview_invites"]

    stored, exported = run(scenario())

    assert [row["pledged_at"] for row in exported] == [stored.pledged_at]
    assert stored.pledged_at is not None


def test_a_deleted_accounts_pending_team_invites_go_and_are_in_its_data_until_then(run):
    from app.storage import members

    async def scenario():
        company = await companies.create(f"Acme {uuid.uuid4()}", "ann", "ann@example.com")
        email = f"bo-{uuid.uuid4().hex[:8]}@example.com"
        other = f"cy-{uuid.uuid4().hex[:8]}@example.com"
        sender = {"company": company.name, "inviter": "ann@example.com", "language": "en"}
        await members.add(company.id, email.upper(), "admin", sender)
        await members.add(company.id, other, "viewer", sender)
        exported = await accounts.export("bo", email)
        # An unverified account's email is empty: it matches no one.
        await accounts.forget_member_invites("")
        await accounts.forget_member_invites(email)
        left = await members.list_for_company(company.id, 0, 10)

        return company.name, exported["company_invitations"], left, other

    name, exported, left, other = run(scenario())

    assert [(row["company"], row["role"]) for row in exported] == [(name, "admin")]
    assert {row.invited_email for row in left if row.user_id is None} == {other}


def test_a_candidates_data_includes_their_extra_time_and_when_they_started(run):
    async def scenario():
        company = await companies.create(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        interview = await interviews.create(company.id, uuid.uuid4(), "en", 60)
        email = f"time-{uuid.uuid4().hex[:8]}@example.com"
        invite, _ = await invites.upsert(interview.id, email, "Backend", "Acme", "en")
        await invites.set_extra_time(invite.id, 30)
        await invite_progress.start(invite.id, f"u-{invite.id}")
        [row] = (await accounts.export(f"u-{invite.id}", email))["interview_invites"]

        return await invites.get(invite.id), row

    stored, row = run(scenario())

    assert (row["extra_time"], row["started_at"]) == (30, stored.started_at)
    assert row["started_at"] is not None and row["finished_at"] is None
