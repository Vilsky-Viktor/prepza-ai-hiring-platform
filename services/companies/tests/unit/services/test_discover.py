"""Inviting from Discover goes through the usual invite, to the account's address, only while
the person is open to offers (services/discover.py; who may ask: test_discover_access.py)."""

import asyncio
import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from prepza_common.auth.user import User

from companies.integrations import accounts, billing, rounds
from companies.services import candidate_invites, discover
from companies.services import outbox as outbox_service

OWNER = User(uid="bob", email="bob@example.com", email_verified=True)
COMPANY = SimpleNamespace(id=uuid.uuid4())
INTERVIEW = SimpleNamespace(id=uuid.uuid4(), company_id=COMPANY.id, set_id=uuid.uuid4())


@pytest.fixture
def invited(monkeypatch):
    sent = []

    async def paid(company_id):
        return True

    async def ready(interview, user_id):
        return interview

    async def open_profile(user_id):
        return {"user_id": user_id, "name": "Ann Lee"} if user_id == "ann" else None

    async def account(user_id):
        return {"user_id": user_id, "email": f"{user_id}@example.com"}

    async def invite(interview, company, user, email, name):
        sent.append((interview.id, user.uid, email, name))

    async def flush():
        return None

    monkeypatch.setattr(billing, "company_paid", paid)
    monkeypatch.setattr(discover, "ready_for_invites", ready)
    monkeypatch.setattr(rounds, "open_profile", open_profile)
    monkeypatch.setattr(accounts, "account", account)
    monkeypatch.setattr(candidate_invites, "invite", invite)
    monkeypatch.setattr(outbox_service, "flush_quietly", flush)

    return sent


def test_an_open_person_is_invited_at_their_accounts_address_by_their_shared_name(invited):
    asyncio.run(discover.invite(INTERVIEW, COMPANY, OWNER, "ann"))

    assert invited == [(INTERVIEW.id, "bob", "ann@example.com", "Ann Lee")]


def test_someone_no_longer_open_to_offers_cant_be_invited(invited):
    with pytest.raises(HTTPException) as refused:
        asyncio.run(discover.invite(INTERVIEW, COMPANY, OWNER, "turned-off"))

    assert refused.value.status_code == 404
    assert invited == []


def test_a_company_that_never_topped_up_sees_nobody(monkeypatch, invited):
    async def unreachable(company_id):
        return False

    monkeypatch.setattr(billing, "company_paid", unreachable)

    with pytest.raises(HTTPException) as refused:
        asyncio.run(discover.people(INTERVIEW, 0, 20))

    assert refused.value.status_code == 403
