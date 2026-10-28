import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException

from companies.api.v1 import schedules
from companies.constants.audit import AUDIT_RETENTION_DAYS
from companies.constants.invites import InviteStatus
from companies.constants.roles import Role
from companies.integrations import billing, rounds
from companies.models.companies import Company, Member
from companies.repositories import accounts, audit
from companies.services import accounts as account_service
from companies.services import company_deletion, retention

INTERVIEW_ID = uuid.uuid4()


def membership(role, owners):
    company = Company(id=uuid.uuid4(), name="Acme")
    member = Member(id=uuid.uuid4(), company_id=company.id, user_id="ann", role=role)

    return member, company, owners


@pytest.fixture
def calls(monkeypatch):
    done = []

    async def delete_company(company_id):
        done.append(("company", company_id))

    async def remove_member(session, member_id):
        done.append(("member", member_id))

    async def candidate_invites(session, user_id, email):
        done.append(("candidate", user_id, email))

        return []

    monkeypatch.setattr(company_deletion, "delete_company", delete_company)
    monkeypatch.setattr(accounts, "remove_member", remove_member)
    monkeypatch.setattr(accounts, "candidate_invites", candidate_invites)

    async def forget_verification(session, email):
        done.append(("verification", email))

    monkeypatch.setattr(accounts, "forget_verification_email", forget_verification)

    async def forget_member_invites(session, email):
        done.append(("team invites", email))

    monkeypatch.setattr(accounts, "forget_member_invites", forget_member_invites)

    async def forget_decisions(sessions, user_id):
        done.append(("audit", user_id))

    monkeypatch.setattr(audit, "forget_user", forget_decisions)

    # Nothing the user owns is shared with others, unless a test says so.
    async def owned(session, user_id):
        return []

    monkeypatch.setattr(accounts, "owned", owned)

    return done


def test_a_company_goes_with_its_only_owner_other_memberships_just_end(calls, monkeypatch):
    sole = membership(Role.OWNER, owners=1)
    shared = membership(Role.OWNER, owners=2)
    admin = membership(Role.ADMIN, owners=1)

    async def memberships(session, user_id):
        return [sole, shared, admin]

    monkeypatch.setattr(accounts, "memberships", memberships)

    asyncio.run(account_service.delete_user("ann", "ann@example.com"))

    assert calls == [
        ("company", sole[1].id),
        ("member", shared[0].id),
        ("member", admin[0].id),
        ("candidate", "ann", "ann@example.com"),
        ("team invites", "ann@example.com"),
        ("verification", "ann@example.com"),
        ("audit", "ann"),
    ]


def test_a_candidate_deleting_their_account_mid_interview_is_settled_as_if_removed(
    calls, monkeypatch
):
    """One who picked an answer is charged, as when a company removes them; one who didn't
    gets the company its credits back. Deleting the account isn't a way out of the charge."""
    picked = SimpleNamespace(id=uuid.uuid4(), status=InviteStatus.IN_PROCESS, hold_key="h1")
    opened = SimpleNamespace(id=uuid.uuid4(), status=InviteStatus.IN_PROCESS, hold_key="h2")
    waiting = SimpleNamespace(id=uuid.uuid4(), status=InviteStatus.INVITED, hold_key="h3")
    settled = []

    async def unfinished(session, user_id, email):
        return [picked, opened, waiting]

    async def scores(invite_ids):
        return {str(picked.id): {"picked": 2}, str(opened.id): {"picked": 0}}

    async def charge(key):
        settled.append(("charged", key))

    async def release(key):
        settled.append(("released", key))

    async def no_memberships(session, user_id):
        return []

    monkeypatch.setattr(accounts, "memberships", no_memberships)
    monkeypatch.setattr(accounts, "unfinished_invites", unfinished)
    monkeypatch.setattr(rounds, "invite_scores", scores)
    monkeypatch.setattr(billing, "charge_candidate", charge)
    monkeypatch.setattr(billing, "release_candidate", release)

    asyncio.run(account_service.delete_user("ann", "ann@example.com"))

    assert settled == [("charged", "h1"), ("released", "h2"), ("released", "h3")]


def test_an_owner_of_a_company_others_joined_cant_delete_their_account_yet(calls, monkeypatch):
    """The company would go with its members' access and its credits: nothing is deleted, and
    another member is made owner first (or the company deleted)."""
    shared = Company(id=uuid.uuid4(), name="Acme")

    async def owned(session, user_id):
        return [(shared, True)]

    async def memberships(session, user_id):
        return [membership(Role.OWNER, owners=1)]

    monkeypatch.setattr(accounts, "owned", owned)
    monkeypatch.setattr(accounts, "memberships", memberships)

    with pytest.raises(HTTPException) as refused:
        asyncio.run(account_service.delete_user("ann", "ann@example.com"))

    assert refused.value.status_code == 409
    assert calls == []


def test_retention_deletes_results_and_holds_before_the_invites_in_batches(monkeypatch):
    done = []
    expired = uuid.uuid4()
    batches = [
        [
            (
                expired,
                INTERVIEW_ID,
                "ann@example.com",
                InviteStatus.IN_PROCESS,
                f"{INTERVIEW_ID}:ann-key",
            )
        ],
        [],
    ]

    async def expired_invites(session, before, limit):
        return batches.pop(0)

    async def release(key):
        done.append(("billing", key))

    async def delete_sessions(invite_ids):
        done.append(("rounds", invite_ids))

    async def delete_invites(session, invite_ids):
        done.append(("invites", invite_ids))

    monkeypatch.setattr(accounts, "expired_invites", expired_invites)
    monkeypatch.setattr(rounds, "delete_invite_sessions", delete_sessions)
    monkeypatch.setattr(accounts, "delete_invites", delete_invites)
    monkeypatch.setattr(billing, "release_candidate", release)

    assert asyncio.run(retention.delete_expired_candidates()) == 1
    # A candidate stuck in process gives their credits back as they go.
    assert done == [
        ("rounds", [expired]),
        ("billing", f"{INTERVIEW_ID}:ann-key"),
        ("invites", [expired]),
    ]


def test_retention_keeps_the_invites_when_rounds_fails(monkeypatch):
    deleted = []

    async def expired_invites(session, before, limit):
        return [(uuid.uuid4(), INTERVIEW_ID, "ann@example.com", InviteStatus.INVITED)]

    async def rounds_down(invite_ids):
        raise httpx.ConnectError("rounds is down")

    async def delete_invites(session, invite_ids):
        deleted.append(invite_ids)

    monkeypatch.setattr(accounts, "expired_invites", expired_invites)
    monkeypatch.setattr(rounds, "delete_invite_sessions", rounds_down)
    monkeypatch.setattr(accounts, "delete_invites", delete_invites)

    with pytest.raises(httpx.ConnectError):
        asyncio.run(retention.delete_expired_candidates())

    assert deleted == []


def test_cloud_scheduler_runs_retention_through_its_route(client, monkeypatch):
    async def expired_invites(session, before, limit):
        return []

    cutoffs = []

    async def delete_before(session, before):
        cutoffs.append(before)

        return 0

    async def forget(sessionmaker, model, before):
        cutoffs.append(before)

        return 0

    monkeypatch.setattr(accounts, "expired_invites", expired_invites)
    monkeypatch.setattr(audit, "delete_before", delete_before)
    monkeypatch.setattr(schedules.processed_events, "forget", forget)

    assert client.post("/internal/schedules/retention").status_code == 204
    # The action log goes after 12 months; the notes of processed events after Pub/Sub's
    # redeliveries.
    assert len(cutoffs) == 2
    assert AUDIT_RETENTION_DAYS == 365
    assert timedelta(days=364) < datetime.now(UTC) - cutoffs[0] < timedelta(days=366)
    assert timedelta(days=7) < datetime.now(UTC) - cutoffs[1] < timedelta(days=9)
