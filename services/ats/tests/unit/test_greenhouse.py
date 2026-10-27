import asyncio
import hashlib
import hmac
import json
from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException
from prepza_common.http import http
from prepza_common.redis import memory_cache

from app.constants.ats import GREENHOUSE_API, GREENHOUSE_TOKEN_URL, AtsProvider
from app.helpers.ats import greenhouse_signed
from app.integrations import ats_clients, greenhouse, workable
from app.integrations.errors import KeyRejected

NEXT = GREENHOUSE_API + "/jobs?cursor=2"


@pytest.fixture(autouse=True)
def no_tokens(monkeypatch):
    """Tokens are kept per credential across calls: each test starts without any."""
    monkeypatch.setattr(memory_cache, "_entries", {})


@pytest.fixture
def harvest(monkeypatch):
    """Greenhouse, replaced: tokens numbered as they're issued, `answers` by path (a status, or a
    (status, json, headers) tuple), every request recorded."""
    state = {"issued": 0, "token": 200, "answers": {}, "requests": []}

    def handler(request):
        state["requests"].append(request)

        if str(request.url) == GREENHOUSE_TOKEN_URL:
            if state["token"] != 200:
                return httpx.Response(state["token"])

            state["issued"] += 1

            return httpx.Response(
                200, json={"access_token": f"t{state['issued']}", "expires_in": 3600}
            )

        answer = state["answers"].get(request.url.path, (200, [], {}))

        if callable(answer):
            answer = answer(request)

        if isinstance(answer, int):
            return httpx.Response(answer)

        code, body, headers = answer

        return httpx.Response(code, json=body, headers=headers)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    monkeypatch.setattr(http, "get_client", lambda: client)

    return state


def calls(state):
    """The Harvest calls (not the token requests), as (method, path, bearer)."""
    return [
        (request.method, request.url.path, request.headers["authorization"])
        for request in state["requests"]
        if str(request.url) != GREENHOUSE_TOKEN_URL
    ]


def test_a_token_is_asked_for_with_the_credential_once_and_reused(harvest):
    asyncio.run(greenhouse.check("id", "secret"))
    asyncio.run(greenhouse.check("id", "secret"))

    token_request = harvest["requests"][0]
    assert token_request.headers["authorization"].startswith("Basic ")
    assert token_request.content == b"grant_type=client_credentials"
    assert harvest["issued"] == 1
    assert calls(harvest) == [("GET", "/v3/jobs", "Bearer t1")] * 2


def test_a_kept_token_never_passes_a_check_with_another_secret(harvest):
    # One company's credential is checked and its token kept; another company sends the same
    # client id with a wrong secret: Greenhouse is asked again, and refuses it.
    asyncio.run(greenhouse.check("id", "secret"))
    harvest["token"] = 401

    with pytest.raises(KeyRejected):
        asyncio.run(greenhouse.check("id", "wrong"))

    assert calls(harvest) == [("GET", "/v3/jobs", "Bearer t1")]


def test_a_token_near_its_expiry_is_renewed(harvest, monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(memory_cache, "time", SimpleNamespace(monotonic=lambda: now[0]))
    asyncio.run(greenhouse.check("id", "secret"))
    now[0] += 3600
    asyncio.run(greenhouse.check("id", "secret"))

    assert harvest["issued"] == 2


def test_a_401_renews_the_token_once_and_tries_again(harvest):
    harvest["answers"]["/v3/jobs"] = lambda request: (
        401 if request.headers["authorization"] == "Bearer t1" else (200, [], {})
    )
    asyncio.run(greenhouse.check("id", "secret"))

    assert calls(harvest) == [("GET", "/v3/jobs", "Bearer t1"), ("GET", "/v3/jobs", "Bearer t2")]


@pytest.mark.parametrize("refusal", [400, 401, 403])
def test_a_refused_credential_is_a_rejected_key(harvest, refusal):
    harvest["token"] = refusal

    with pytest.raises(KeyRejected):
        asyncio.run(greenhouse.check("id", "bad"))


@pytest.mark.parametrize("refusal", [400, 401, 403, 404])
def test_a_check_refused_even_with_a_fresh_token_is_a_rejected_key(harvest, refusal):
    harvest["answers"]["/v3/jobs"] = refusal

    with pytest.raises(KeyRejected):
        asyncio.run(greenhouse.check("id", "secret"))


def test_a_failing_greenhouse_is_a_502(harvest):
    harvest["answers"]["/v3/jobs"] = 500

    with pytest.raises(HTTPException) as failed:
        asyncio.run(greenhouse.check("id", "secret"))

    assert failed.value.status_code == 502

    harvest["answers"].clear()
    harvest["token"] = 500

    with pytest.raises(HTTPException) as failed:
        asyncio.run(greenhouse.check("other-id", "secret"))

    assert failed.value.status_code == 502


def test_open_jobs_are_read_page_by_page_following_the_link_header(harvest):
    def jobs(request):
        if "cursor" in request.url.params:
            # The next page's address carries its own query.
            assert "status" not in request.url.params

            return 200, {"data": [{"id": 2, "name": "Support"}]}, {}

        assert request.url.params["status"] == "open"

        return 200, [{"id": 1, "name": "Accountant"}], {"Link": f'<{NEXT}>; rel="next"'}

    harvest["answers"]["/v3/jobs"] = jobs

    assert asyncio.run(greenhouse.jobs("id", "secret")) == [
        {"id": "1", "name": "Accountant"},
        {"id": "2", "name": "Support"},
    ]


def test_a_next_page_off_greenhouses_api_is_never_called_with_the_token(harvest):
    elsewhere = "https://attacker.example/v3/jobs?cursor=2"
    harvest["answers"]["/v3/jobs"] = (200, [], {"Link": f'<{elsewhere}>; rel="next"'})

    with pytest.raises(HTTPException) as refused:
        asyncio.run(greenhouse.jobs("id", "secret"))

    assert refused.value.status_code == 502
    assert "attacker.example" not in {request.url.host for request in harvest["requests"]}


def test_a_jobs_stages_and_text_come_from_greenhouse(harvest):
    harvest["answers"]["/v3/job_interview_stages"] = (
        200,
        {"data": [{"id": 7, "name": "Test"}]},
        {},
    )
    harvest["answers"]["/v3/jobs"] = (200, [{"id": 1, "name": "Accountant"}], {})
    harvest["answers"]["/v3/job_posts"] = (200, [{"content": "<p>Close</p>"}, {}], {})

    assert asyncio.run(greenhouse.stages("id", "secret", "1")) == [{"id": "7", "name": "Test"}]
    assert asyncio.run(greenhouse.job("id", "secret", "1")) == {
        "name": "Accountant",
        "sections": ["<p>Close</p>", ""],
    }
    assert harvest["requests"][1].url.params["job_ids"] == "1"


@pytest.mark.parametrize(
    ("candidate_id", "member", "extra"),
    [
        ("11:22", "33", {"application_id": 22, "user_id": 33}),
        ("11", None, {}),
    ],
)
def test_a_note_goes_on_the_candidate_and_application(harvest, candidate_id, member, extra):
    asyncio.run(greenhouse.comment("id", "secret", candidate_id, member, "Grade: 82%"))

    [note] = [request for request in harvest["requests"] if request.url.path == "/v3/notes"]
    assert note.method == "POST"
    assert json.loads(note.content) == {
        "candidate_id": 11,
        "body": "Grade: 82%",
        "note_type": "NOTE",
        "visibility": "public",
        **extra,
    }


@pytest.mark.parametrize(("answer", "raised"), [(400, 502), (404, 404)])
def test_a_note_greenhouse_doesnt_take_isnt_a_rejected_key(harvest, answer, raised):
    # Only checking a credential takes a 400 or 404 as a refusal; on a note it's that note.
    harvest["answers"]["/v3/notes"] = answer

    with pytest.raises(HTTPException) as failed:
        asyncio.run(greenhouse.comment("id", "secret", "11:22", None, "Grade: 82%"))

    assert failed.value.status_code == raised


def test_only_bodies_signed_with_the_secret_key_count():
    body = b'{"action": "ping"}'
    digest = hmac.new(b"secret", body, hashlib.sha256).hexdigest()

    assert greenhouse_signed("secret", body, f"sha256 {digest}")
    assert not greenhouse_signed("other", body, f"sha256 {digest}")
    assert not greenhouse_signed("secret", body + b" ", f"sha256 {digest}")
    assert not greenhouse_signed("secret", body, "")


def test_each_ats_has_its_client():
    assert ats_clients.client("workable") is workable
    assert ats_clients.client("greenhouse") is greenhouse
    assert set(ats_clients.CLIENTS) == set(AtsProvider)

    with pytest.raises(ValueError):
        ats_clients.client("lever")


@pytest.mark.parametrize(
    ("answer", "can"),
    [
        ((200, {"active": True, "scope": "harvest:jobs:list harvest:notes:create"}, {}), True),
        ((200, {"active": True, "scope": "harvest:jobs:list"}, {}), False),
        # Anything less certain lets it connect: a refused note tells later.
        ((200, {"active": False}, {}), True),
        ((200, {"active": True}, {}), True),
        (500, True),
        ((200, ["unexpected"], {}), True),
    ],
)
def test_a_credential_is_refused_only_when_greenhouse_says_it_cant_write_notes(
    harvest, answer, can
):
    harvest["answers"]["/introspect"] = answer

    assert asyncio.run(greenhouse.can_write("id", "secret")) is can

    [introspect] = [r for r in harvest["requests"] if r.url.path == "/introspect"]
    assert introspect.headers["authorization"].startswith("Basic ")
    assert b"token=t1" in introspect.content
