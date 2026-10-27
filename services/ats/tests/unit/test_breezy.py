import asyncio
import hashlib
import hmac
import json

import httpx
import pytest
from fastapi import HTTPException
from prepza_common.http import http

from app.helpers.ats import breezy_signed
from app.integrations import ats_clients, breezy
from app.integrations.errors import KeyRejected

API = "https://api.breezy.hr/v3"


@pytest.fixture
def api(monkeypatch):
    """Breezy HR, replaced: `answers` by path (a status, a json body, or a function of the
    request), every request recorded."""
    state = {"answers": {}, "requests": []}

    def handler(request):
        state["requests"].append(request)
        answer = state["answers"].get(request.url.path, {})

        if callable(answer):
            answer = answer(request)

        if isinstance(answer, int):
            return httpx.Response(answer)

        return httpx.Response(200, json=answer)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    monkeypatch.setattr(http, "get_client", lambda: client)

    return state


def test_calls_carry_the_key_as_it_is(api):
    api["answers"]["/v3/company/c1/positions"] = []
    asyncio.run(breezy.check("c1", "secret-key"))

    [request] = api["requests"]
    assert str(request.url) == API + "/company/c1/positions?state=published"
    assert request.headers["authorization"] == "secret-key"


@pytest.mark.parametrize("refusal", [401, 403])
def test_a_refused_key_is_a_rejected_key(api, refusal):
    api["answers"]["/v3/companies"] = refusal

    with pytest.raises(KeyRejected):
        asyncio.run(breezy.company("bad"))


@pytest.mark.parametrize("failure", [500, 503])
def test_a_failing_or_unreachable_breezy_is_a_502(api, failure):
    api["answers"]["/v3/companies"] = failure

    with pytest.raises(HTTPException) as failed:
        asyncio.run(breezy.company("key"))

    assert (failed.value.status_code, failed.value.detail) == (502, "Breezy HR didn't answer")

    def unreachable(request):
        raise httpx.ConnectError("down")

    api["answers"]["/v3/companies"] = unreachable

    with pytest.raises(HTTPException) as failed:
        asyncio.run(breezy.company("key"))

    assert failed.value.status_code == 502


def test_the_company_is_the_keys_persons_first_one(api):
    api["answers"]["/v3/companies"] = [{"_id": "c1", "name": "Acme"}, {"_id": "c2"}]

    assert asyncio.run(breezy.company("key")) == {"id": "c1", "name": "Acme"}

    api["answers"]["/v3/companies"] = []

    assert asyncio.run(breezy.company("key")) is None


def test_jobs_are_the_published_positions(api):
    api["answers"]["/v3/company/c1/positions"] = [
        {"_id": "p1", "name": "Accountant"},
        {"_id": "p2"},
    ]

    assert asyncio.run(breezy.jobs("c1", "key")) == [
        {"id": "p1", "name": "Accountant"},
        {"id": "p2", "name": ""},
    ]
    [request] = api["requests"]
    assert request.url.params["state"] == "published"


def test_stages_are_the_positions_pipelines(api):
    api["answers"]["/v3/company/c1/position/p1"] = {"pipeline_id": "pl1"}
    api["answers"]["/v3/company/c1/pipeline/pl1"] = {
        "pipeline": [{"id": "applied", "name": "Applied"}, {"id": "s2", "name": "Test"}]
    }

    assert asyncio.run(breezy.stages("c1", "key", "p1")) == [
        {"id": "applied", "name": "Applied"},
        {"id": "s2", "name": "Test"},
    ]


def test_a_position_without_a_pipeline_has_no_stages(api):
    api["answers"]["/v3/company/c1/position/p1"] = {"name": "Accountant"}

    assert asyncio.run(breezy.stages("c1", "key", "p1")) == []
    assert len(api["requests"]) == 1


def test_a_job_is_its_name_and_description(api):
    api["answers"]["/v3/company/c1/position/p1"] = {
        "name": "Accountant",
        "description": "<p>Join</p>",
    }

    assert asyncio.run(breezy.job("c1", "key", "p1")) == {
        "name": "Accountant",
        "sections": ["<p>Join</p>"],
    }

    api["answers"]["/v3/company/c1/position/p1"] = {"description": None}

    assert asyncio.run(breezy.job("c1", "key", "p1")) == {"name": "", "sections": [""]}


def test_a_note_goes_on_the_candidates_activity_in_the_position(api):
    asyncio.run(breezy.comment("c1", "key", "p1:cand1", None, "Grade: 82%"))

    [note] = api["requests"]
    assert (note.method, str(note.url)) == (
        "POST",
        API + "/company/c1/position/p1/candidate/cand1/stream",
    )
    assert json.loads(note.content) == {"body": "Grade: 82%"}


def test_the_web_hook_is_created_for_stage_changes_and_deleted_by_its_id(api):
    api["answers"]["/v3/company/c1/webhook_endpoints"] = {"id": "w1", "secret": "s3cret"}

    assert asyncio.run(breezy.subscribe("c1", "key", "https://x/hook")) == ("w1", "s3cret")

    asyncio.run(breezy.unsubscribe("c1", "key", "w1"))

    created, deleted = api["requests"]
    assert created.method == "POST"
    assert json.loads(created.content) == {
        "url": "https://x/hook",
        "description": "prepza",
        "events": ["candidateStatusUpdated"],
    }
    assert (deleted.method, str(deleted.url)) == (
        "DELETE",
        API + "/company/c1/webhook_endpoint/w1",
    )


def signature(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_only_the_raw_body_signed_with_the_secret_counts():
    body = b'{"type": "candidateStatusUpdated", "object": {"a": 1}}'
    compact = b'{"type":"candidateStatusUpdated","object":{"a":1}}'

    assert breezy_signed("secret", body, signature("secret", body))
    # The same JSON written another way isn't what was received.
    assert not breezy_signed("secret", body, signature("secret", compact))
    assert breezy_signed("secret", body, f" {signature('secret', body).upper()}\n")
    assert not breezy_signed("other", body, signature("secret", body))
    assert not breezy_signed("secret", body, signature("secret", body + b"x"))
    assert not breezy_signed("secret", body, "")


def test_a_body_that_isnt_json_is_still_checked_as_it_came():
    body = b"not json"

    assert breezy_signed("secret", body, signature("secret", body))
    assert not breezy_signed("secret", body, signature("other", body))


def test_breezy_has_its_client():
    assert ats_clients.client("breezy") is breezy
    assert breezy.KEYS == ("company", "token")


def test_a_position_deleted_in_breezy_is_a_404_not_a_failure(api):
    api["answers"]["/v3/company/c1/position/p1"] = 404

    with pytest.raises(HTTPException) as gone:
        asyncio.run(breezy.job("c1", "key", "p1"))

    assert gone.value.status_code == 404
