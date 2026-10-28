import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from api.handlers import dispatch
from api.repositories import webhooks
from api.services import accounts, manage
from api.services import webhooks as delivery
from tests.unit.conftest import CANDIDATE, COMPANY, INTERVIEW, sign_in

CANDIDATE_DATA = {
    "company_id": str(COMPANY),
    "interview_id": str(INTERVIEW),
    "candidate_invite_id": str(CANDIDATE),
}


@pytest.fixture(autouse=True)
def no_retries_to_drop(monkeypatch):
    async def remove_candidate(session, company_id, interview_id, email):
        pass

    monkeypatch.setattr(accounts.webhook_retries, "remove_candidate", remove_candidate)


def handle(event_type, data, event_id="e1"):
    asyncio.run(dispatch.handle(event_type, data, event_id))


@pytest.mark.parametrize(
    "event_type", ["candidate.started", "candidate.undelivered", "candidate.expired"]
)
def test_a_candidates_event_brings_the_interview_and_the_candidate(endpoints, event_type):
    endpoints["hook"]("https://a.example/x")
    handle(event_type, CANDIDATE_DATA)
    [(_, body, _)] = endpoints["posted"]

    assert body["type"] == event_type
    assert body["data"]["interview"]["id"] == str(INTERVIEW)
    assert body["data"]["candidate"]["id"] == str(CANDIDATE)


def test_a_removed_candidate_is_told_by_who_it_was(endpoints):
    endpoints["hook"]("https://a.example/x")
    handle("candidate.removed", {**CANDIDATE_DATA, "email": "ann@example.com"})
    [(_, body, _)] = endpoints["posted"]

    assert body["type"] == "candidate.removed"
    assert body["data"] == {
        "interview_id": str(INTERVIEW),
        "candidate_id": str(CANDIDATE),
        "email": "ann@example.com",
    }


def test_events_from_before_their_fields_existed_tell_nobody(endpoints):
    # Companies' older events, still in flight: no candidate id, no company.
    endpoints["hook"]("https://a.example/x")
    handle(
        "candidate.removed",
        {"company_id": str(COMPANY), "interview_id": str(INTERVIEW), "email": "a@b.c"},
    )
    handle("interview.ready", {"interview_id": str(INTERVIEW)}, "e2")

    assert endpoints["posted"] == []


def test_an_interview_ready_brings_the_interview(endpoints):
    endpoints["hook"]("https://a.example/x")
    handle("interview.ready", {"interview_id": str(INTERVIEW), "company_id": str(COMPANY)})
    [(_, body, _)] = endpoints["posted"]

    assert body["type"] == "interview.ready"
    assert body["data"]["interview"]["id"] == str(INTERVIEW)


def test_each_send_is_logged_with_how_it_went(endpoints):
    good = endpoints["hook"]("https://a.example/x")
    down = endpoints["hook"]("https://down.example/x")
    endpoints["failing"].add("https://down.example/x")
    handle("candidate.started", CANDIDATE_DATA)

    assert sorted(endpoints["log"], key=lambda row: row[3]) == [
        (down.id, "candidate.started", False, "ConnectError"),
        (good.id, "candidate.started", True, "delivered"),
    ]


def test_a_test_event_is_signed_sent_and_logged(endpoints):
    hook = endpoints["hook"]("https://a.example/x")

    assert asyncio.run(delivery.test(hook)) is True

    [(_, body, signature)] = endpoints["posted"]

    assert body["type"] == "test" and body["data"] == {}
    assert ",v1=" in signature
    assert endpoints["log"] == [(hook.id, "test", True, "delivered")]


@pytest.fixture
def hook_routes(monkeypatch, endpoints):
    """The company's web hooks for the API page's routes, with one logged send; the tests sent
    are in `hook.tested_by`, as the action log gets them."""
    hook = endpoints["hook"]("https://a.example/x")
    hook.tested_by = []

    async def get(session, company_id, webhook_id):
        return hook if company_id == COMPANY and webhook_id == hook.id else None

    async def latest(session, webhook_id):
        sent = datetime(2026, 10, 15, tzinfo=UTC)

        return [SimpleNamespace(event_type="test", ok=True, result="delivered", at=sent)]

    async def tested(session, found, user_id):
        found.tested_by.append(user_id)

    monkeypatch.setattr(webhooks, "get", get)
    monkeypatch.setattr(webhooks, "tested", tested)
    monkeypatch.setattr(manage.webhook_log_store, "latest", latest)

    return hook


def test_an_owner_sends_a_test_event_and_reads_the_log(client, companies_api, hook_routes):
    sign_in("u1")
    base = f"/manage/webhooks/{hook_routes.id}"

    assert client.post(f"{base}/test", params={"company_id": str(COMPANY)}).json() == {"ok": True}
    assert hook_routes.tested_by == ["u1"]
    assert client.get(f"{base}/log", params={"company_id": str(COMPANY)}).json() == [
        {"event_type": "test", "ok": True, "result": "delivered", "at": "2026-10-15T00:00:00Z"}
    ]


def test_only_editors_send_test_events_and_only_to_their_companys_hooks(
    client, companies_api, hook_routes
):
    companies_api["roles"]["v1"] = "viewer"
    sign_in("v1")
    params = {"company_id": str(COMPANY)}

    assert client.post(f"/manage/webhooks/{hook_routes.id}/test", params=params).status_code == 403
    # A viewer reads the log, like the rest of the API page.
    assert client.get(f"/manage/webhooks/{hook_routes.id}/log", params=params).status_code == 200

    sign_in("u1")
    other = "00000000-0000-4000-8000-000000000000"

    assert client.post(f"/manage/webhooks/{other}/test", params=params).status_code == 404
    assert hook_routes.tested_by == []


def test_test_events_past_the_hourly_limit_are_refused_and_not_sent(
    client, companies_api, hook_routes, monkeypatch
):
    counted = []

    async def one_left(redis, key, name, message=None, **who):
        counted.append((key, name, who["user_id"]))

        if len(counted) > 1:
            raise HTTPException(429, "Too many requests. Try again later.")

    monkeypatch.setattr(manage, "hit_or_skip", one_left)
    sign_in("u1")
    url = f"/manage/webhooks/{hook_routes.id}/test"
    params = {"company_id": str(COMPANY)}

    assert client.post(url, params=params).status_code == 200
    assert client.post(url, params=params).status_code == 429
    assert hook_routes.tested_by == ["u1"]
    assert counted[0] == (f"rate:webhook-tests:{COMPANY}", "WEBHOOK_TESTS_PER_HOUR", "u1")


def test_an_event_says_when_its_change_happened(endpoints):
    endpoints["hook"]("https://a.example/x")
    happened = datetime(2026, 10, 15, 8, 30, tzinfo=UTC)
    asyncio.run(dispatch.handle("candidate.started", CANDIDATE_DATA, "e1", happened))
    [(_, body, _)] = endpoints["posted"]

    assert body["occurred_at"] == "2026-10-15T08:30:00+00:00"
