"""A change to a candidate is one save with its line in the action log: an invite and its
email, a removal, a new name or extra time, an emailed report. When the log's line fails,
nothing else is kept, so the retry finds the whole action still to do."""

import uuid

import pytest
from prepza_common.auth.user import User
from sqlalchemy import func, select

from companies.constants.events import REPORT_SHARED
from companies.constants.roles import Role
from companies.core.db import Session
from companies.integrations import billing, rounds
from companies.models.outbox import OutboxEvent
from companies.repositories import audit, companies, interviews, invites
from companies.services import candidate_changes, candidate_invites, report_emails
from companies.services import outbox as outbox_service
from tests.integration import factories
from tests.integration.broken import DatabaseWentAway, broken
from tests.integration.transactions import transaction


@pytest.fixture(autouse=True)
def calls_elsewhere(monkeypatch):
    """Billing and rounds are other services; the report's limits are counted elsewhere."""

    async def nothing(*args, **kwargs):
        return None

    async def no_scores(invite_ids):
        return {}

    monkeypatch.setattr(billing, "release_candidate", nothing)
    monkeypatch.setattr(rounds, "invite_scores", no_scores)
    monkeypatch.setattr(rounds, "delete_invite_sessions", nothing)
    monkeypatch.setattr(report_emails, "allow_report_email", nothing)
    monkeypatch.setattr(outbox_service, "flush_quietly", nothing)
    monkeypatch.setattr(audit, "record", broken)
    monkeypatch.setattr(audit, "record_interview", broken)


async def a_candidate() -> tuple:
    """A company's interview, its owner signed in, and one invited candidate."""
    tag = uuid.uuid4()
    company = await factories.company(f"Saves {tag}", f"ann-{tag}", f"ann-{tag}@example.com")
    interview = await transaction(interviews.create, company.id, uuid.uuid4(), "en", 60)
    invite, _ = await transaction(
        invites.upsert, interview.id, f"cara-{tag}@example.com", "Backend", "Acme", "en"
    )
    user = User(uid=f"ann-{tag}", email=f"ann-{tag}@example.com", email_verified=True)

    return await transaction(companies.get, company.id), interview, invite, user


def test_an_invite_whose_log_line_fails_isnt_saved(run):
    async def scenario():
        company, interview, _, user = await a_candidate()
        email = f"dan-{uuid.uuid4()}@example.com"

        with pytest.raises(DatabaseWentAway):
            await candidate_invites.save(
                interview, company, email, "Backend", (user.uid, "candidate_invited", None)
            )

        return await transaction(invites.find, interview.id, email)

    assert run(scenario()) is None


def test_a_removal_whose_log_line_fails_keeps_the_candidate(run):
    async def scenario():
        _, interview, invite, user = await a_candidate()

        with pytest.raises(DatabaseWentAway):
            await candidate_changes.remove(interview, invite, user.uid, None)

        return await transaction(invites.get, invite.id) is not None

    assert run(scenario()) is True


@pytest.mark.parametrize("values", [{"name": "Cara Diaz"}, {"extra_time": 30}])
def test_a_change_whose_log_line_fails_isnt_written(run, values):
    async def scenario():
        _, interview, invite, user = await a_candidate()

        with pytest.raises(DatabaseWentAway):
            await candidate_changes.change(interview, invite, values, user.uid)

        found = await transaction(invites.get, invite.id)

        return (invite.name, invite.extra_time), (found.name, found.extra_time)

    before, after = run(scenario())

    assert after == before


@pytest.mark.parametrize("whose", ["candidate", "interview"])
def test_a_report_whose_log_line_fails_isnt_emailed(run, whose):
    async def scenario():
        company, interview, invite, user = await a_candidate()
        member = next(item for item in company.members if item.role == Role.OWNER)
        email = f"hm-{uuid.uuid4()}@example.com"

        with pytest.raises(DatabaseWentAway):
            if whose == "candidate":
                await report_emails.email_candidate_report(
                    user, company, member, interview, invite, email, "pdf", None
                )
            else:
                await report_emails.email_interview_report(
                    user, company, member, interview, email, "pdf", None
                )

        async with Session() as session:
            return await session.scalar(
                select(func.count())
                .select_from(OutboxEvent)
                .where(
                    OutboxEvent.event_type == REPORT_SHARED,
                    OutboxEvent.data["email"].astext == email,
                )
            )

    assert run(scenario()) == 0
