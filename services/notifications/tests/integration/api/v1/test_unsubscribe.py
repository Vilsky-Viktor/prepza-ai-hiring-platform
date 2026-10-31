import hashlib
import json
import uuid

import httpx
import pytest
from event_pushes import push
from sqlalchemy import func, select
from testee_common.http import http

from notifications.config import settings
from notifications.constants.unsubscribe import UnsubscribeType
from notifications.core.db import Session
from notifications.helpers.unsubscribe import address_hash, candidate_token, sign, user_token
from notifications.models.opt_outs import CandidateOptOut
from notifications.repositories import opt_outs
from tests.integration.factories import api
from tests.integration.transactions import transaction


def invite(company_id: str, email: str = "ann@example.com") -> dict:
    return {
        "invite_id": str(uuid.uuid4()),
        "company_id": company_id,
        "email": email,
        "token": "t",
        "title": "Backend",
        "company": "Acme",
        "language": "en",
    }


@pytest.fixture
def outside(monkeypatch):
    """Resend, companies and accounts at the HTTP boundary: every request is recorded."""
    requests = []

    def answer(request: httpx.Request) -> httpx.Response:
        requests.append(request)

        if request.url.host == "api.resend.com":
            return httpx.Response(200, json={"id": "e-1"})

        return httpx.Response(200, json={})

    monkeypatch.setattr(settings, "resend_api_key", "re_test")
    monkeypatch.setattr(settings, "companies_url", "http://companies")
    monkeypatch.setattr(settings, "accounts_url", "http://accounts")
    monkeypatch.setattr(
        http, "get_client", lambda: httpx.AsyncClient(transport=httpx.MockTransport(answer))
    )

    return requests


def sent(requests) -> list[dict]:
    return [json.loads(item.content) for item in requests if item.url.host == "api.resend.com"]


def test_opting_out_of_a_company_twice_stores_it_once_and_stops_its_invites_and_reminders(
    run, outside
):
    company = str(uuid.uuid4())
    data = invite(company)
    link = candidate_token(data, UnsubscribeType.COMPANY, settings.email_link_secret)

    async def scenario():
        async with api() as client:
            codes = [(await client.post(f"/unsubscribe/{link}")).status_code for _ in range(2)]
            await client.post("/internal/events", json=push("candidate.invited", data, "o-1"))
            await client.post("/internal/events", json=push("candidate.reminded", data, "o-2"))
            # Another company still reaches the same address.
            other = invite(str(uuid.uuid4()), "ANN@example.com")
            await client.post("/internal/events", json=push("candidate.invited", other, "o-3"))

        async with Session() as session:
            rows = await session.scalar(
                select(func.count()).where(CandidateOptOut.company_id == company)
            )

        return codes, rows

    assert run(scenario()) == ([204, 204], 1)
    assert [email["to"] for email in sent(outside)] == [["ANN@example.com"]]
    # The company sees the invite as undelivered, as with a bounce.
    undelivered = [str(item.url) for item in outside if item.url.host == "companies"]
    assert undelivered == [f"http://companies/internal/invites/{data['invite_id']}/undelivered"]


def test_a_link_sent_before_the_hashes_were_keyed_still_stops_the_companys_invites(run, outside):
    company = str(uuid.uuid4())
    data = invite(company, "old@example.com")
    plain = hashlib.sha256(b"old@example.com").hexdigest()
    payload = {"type": "company", "address": plain, "company_id": company, "company": "Acme"}
    link = sign(payload, settings.email_link_secret)

    async def scenario():
        async with api() as client:
            code = (await client.post(f"/unsubscribe/{link}")).status_code
            await client.post("/internal/events", json=push("candidate.invited", data, "o-1"))

        async with Session() as session:
            stored = await session.scalar(
                select(CandidateOptOut.address).where(CandidateOptOut.company_id == company)
            )

        return code, stored

    code, stored = run(scenario())

    assert code == 204
    # Kept as the keyed hash, never the plain one the old link carried.
    assert stored == address_hash("old@example.com") != plain
    assert sent(outside) == []


def test_stopping_one_invites_reminders_leaves_its_invite_and_other_invites(run, outside):
    company = str(uuid.uuid4())
    first, second = invite(company), invite(company)
    link = candidate_token(first, UnsubscribeType.INVITE_REMINDERS, settings.email_link_secret)

    async def scenario():
        async with api() as client:
            await client.post(f"/unsubscribe/{link}")
            await client.post("/internal/events", json=push("candidate.reminded", first, "o-1"))
            await client.post("/internal/events", json=push("candidate.invited", first, "o-2"))
            await client.post("/internal/events", json=push("candidate.reminded", second, "o-3"))

    run(scenario())

    kinds = [
        next(tag["value"] for tag in email["tags"] if tag["name"] == "kind")
        for email in sent(outside)
    ]
    assert kinds == ["candidate_invite", "candidate_reminder"]
    # The reminder that went out carries the one-click unsubscribe for its own reminders.
    headers = sent(outside)[1]["headers"]
    assert headers["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"
    assert headers["List-Unsubscribe"].startswith(f"<{settings.site_url}/api/notifications/")


def test_a_users_one_click_unsubscribe_turns_accounts_settings_off(run, outside):
    link = user_token("ann", UnsubscribeType.DIGEST, settings.email_link_secret)

    async def scenario():
        async with api() as client:
            return await client.post(
                f"/unsubscribe/{link}",
                content="List-Unsubscribe=One-Click",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

    assert run(scenario()).status_code == 204
    [request] = outside
    assert str(request.url) == "http://accounts/internal/users/ann/unsubscribe"
    assert json.loads(request.content) == {
        "settings": [
            "candidate_finished",
            "invite_undelivered",
            "ats_not_invited",
            "interview_ready",
            "note_added",
        ]
    }


def test_a_deleted_company_takes_its_opt_outs_with_it(run):
    company = str(uuid.uuid4())

    async def scenario():
        await transaction(opt_outs.add, address_hash("ann@example.com"), company)
        await transaction(opt_outs.add, address_hash("bob@example.com"), company, str(uuid.uuid4()))

        async with api() as client:
            await client.post(
                "/internal/events",
                json=push("company.deleted", {"company_id": company}, event_id=None),
            )

        return await transaction(opt_outs.opted_out, address_hash("ann@example.com"), company)

    assert run(scenario()) is False
