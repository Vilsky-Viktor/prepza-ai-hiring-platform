"""A team change is one save with its line in the action log (and its notification): when a
later step fails, the earlier ones aren't kept. An account's deletion forgets its memberships,
candidate invites, team invites and verification proof in one save too."""

import uuid

import pytest
from fake_redis import FakeRedis
from sqlalchemy import func, select
from testee_common.auth.user import User

from companies.constants.events import MEMBER_INVITED
from companies.constants.roles import Role
from companies.core.db import Session
from companies.integrations import billing
from companies.models.companies import Member
from companies.models.outbox import OutboxEvent
from companies.repositories import accounts, audit, companies, interviews, invites
from companies.services import accounts as account_service
from companies.services import members as member_service
from companies.services import outbox as outbox_service
from tests.integration import factories
from tests.integration.broken import DatabaseWentAway, broken
from tests.integration.transactions import transaction


@pytest.fixture(autouse=True)
def calls_elsewhere(monkeypatch):
    """Billing and Redis are other services: a paying company, limits at their defaults."""

    async def paid(company_id):
        return True

    async def nothing(*args, **kwargs):
        return None

    monkeypatch.setattr(billing, "company_paid", paid)
    monkeypatch.setattr(billing, "turn_off_auto_top_up", nothing)
    monkeypatch.setattr(member_service, "get_redis", FakeRedis)
    monkeypatch.setattr(outbox_service, "flush_quietly", nothing)
    monkeypatch.setattr(audit, "record", broken)


async def team() -> tuple:
    """A company with Ann its owner and Bob a joined admin."""
    tag = uuid.uuid4()
    company = await factories.company(f"Team {tag}", f"ann-{tag}", f"ann-{tag}@example.com")
    bob = await factories.member(company.id, f"bob-{tag}@example.com", Role.ADMIN, {})

    async with Session.begin() as session:
        (await session.get(Member, bob.id)).user_id = f"bob-{tag}"

    return await transaction(companies.get, company.id), tag


def by_role(company, role):
    return next(member for member in company.members if member.role == role)


def test_an_invite_whose_log_line_fails_leaves_no_invite_and_no_email(run):
    async def scenario():
        company, tag = await team()
        owner = by_role(company, Role.OWNER)
        user = User(uid=owner.user_id, email=owner.invited_email, email_verified=True)
        email = f"cid-{tag}@example.com"

        with pytest.raises(DatabaseWentAway):
            await member_service.invite(company, user, email, Role.VIEWER)

        async with Session() as session:
            rows = await session.scalar(
                select(func.count()).select_from(Member).where(Member.invited_email == email)
            )
            sent = await session.scalar(
                select(func.count())
                .select_from(OutboxEvent)
                .where(
                    OutboxEvent.event_type == MEMBER_INVITED,
                    OutboxEvent.data["email"].astext == email,
                )
            )

        return rows, sent

    assert run(scenario()) == (0, 0)


@pytest.mark.parametrize("change", ["role", "remove", "owner"])
def test_a_team_change_whose_log_line_fails_isnt_kept(run, change):
    async def scenario():
        company, _ = await team()
        owner, bob = by_role(company, Role.OWNER), by_role(company, Role.ADMIN)

        with pytest.raises(DatabaseWentAway):
            if change == "role":
                await member_service.change_role(company.id, bob, Role.VIEWER, owner.user_id)
            elif change == "remove":
                await member_service.remove(company.id, bob, owner.user_id)
            else:
                await member_service.transfer(company, owner, bob, owner.user_id, None)

        found = await transaction(companies.get, company.id)

        return {member.user_id.split("-")[0]: member.role for member in found.members}

    assert run(scenario()) == {"ann": Role.OWNER, "bob": Role.ADMIN}


def test_a_join_whose_log_line_fails_leaves_the_invite_pending(run):
    async def scenario():
        company, tag = await team()
        cid = await factories.member(company.id, f"cid-{tag}@example.com", Role.VIEWER, {})
        user = User(uid=f"cid-{tag}", email=cid.invited_email, email_verified=True)

        with pytest.raises(DatabaseWentAway):
            await member_service.accept(cid.token, user)

        async with Session() as session:
            return (await session.get(Member, cid.id)).user_id

    assert run(scenario()) is None


def test_an_account_deletion_whose_last_step_fails_keeps_everything_for_the_retry(run, monkeypatch):
    monkeypatch.setattr(accounts, "forget_verification_email", broken)

    async def scenario():
        company, _ = await team()
        bob = by_role(company, Role.ADMIN)
        interview = await transaction(interviews.create, company.id, uuid.uuid4(), "en", 60)
        invite, _ = await transaction(
            invites.upsert, interview.id, bob.invited_email, "Backend", "Acme", "en"
        )

        with pytest.raises(DatabaseWentAway):
            await account_service.forget(bob.user_id, bob.invited_email, [bob.id])

        async with Session() as session:
            member = await session.get(Member, bob.id)

        return member is not None, await transaction(invites.get, invite.id) is not None

    assert run(scenario()) == (True, True)
