import asyncio
import hashlib
import hmac
import json

import httpx
import pytest
from fastapi import HTTPException
from testee_common.http import http

from ats.helpers.ats import recruitee_signed
from ats.integrations import ats_clients, recruitee
from ats.integrations.errors import KeyRejected

API = "https://api.recruitee.com/c/acme"


@pytest.fixture
def api(monkeypatch):
    """Recruitee, replaced: `answers` by path (a status, a json body, or a function of the
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


def test_calls_carry_the_token_to_the_companys_api(api):
    asyncio.run(recruitee.check("acme", "secret-token"))

    [request] = api["requests"]
    assert str(request.url) == API + "/offers?limit=1"
    assert request.headers["authorization"] == "Bearer secret-token"


@pytest.mark.parametrize("refusal", [401, 403, 404])
def test_a_refused_token_or_an_unknown_company_is_a_rejected_key(api, refusal):
    api["answers"]["/c/acme/offers"] = refusal

    with pytest.raises(KeyRejected):
        asyncio.run(recruitee.check("acme", "bad"))


def test_a_failing_or_unreachable_recruitee_is_a_502(api):
    api["answers"]["/c/acme/offers"] = 500

    with pytest.raises(HTTPException) as failed:
        asyncio.run(recruitee.check("acme", "token"))

    assert failed.value.status_code == 502

    def unreachable(request):
        raise httpx.ConnectError("down")

    api["answers"]["/c/acme/offers"] = unreachable

    with pytest.raises(HTTPException) as failed:
        asyncio.run(recruitee.check("acme", "token"))

    assert failed.value.status_code == 502


def test_jobs_are_the_hiring_ones_and_talent_pools_are_left_out(api):
    api["answers"]["/c/acme/offers"] = {
        "offers": [
            {"id": 1, "title": "Accountant", "kind": "job"},
            {"id": 2, "title": "Pool", "kind": "talent_pool"},
            {"id": 3, "title": "Support"},
        ]
    }

    assert asyncio.run(recruitee.jobs("acme", "token")) == [
        {"id": "1", "name": "Accountant"},
        {"id": "3", "name": "Support"},
    ]
    [request] = api["requests"]
    assert request.url.params.get_list("statuses[]") == ["published", "internal"]


def test_stages_come_in_their_pipelines_order(api):
    api["answers"]["/c/acme/offers/1"] = {
        "offer": {
            "pipeline_template": {
                "stages": [
                    {"id": 8, "name": "Offer", "position": 2},
                    {"id": 6, "name": "Applied", "position": 0},
                    {"id": 7, "name": "Test", "position": 1},
                ]
            }
        }
    }

    assert asyncio.run(recruitee.stages("acme", "token", "1")) == [
        {"id": "6", "name": "Applied"},
        {"id": "7", "name": "Test"},
        {"id": "8", "name": "Offer"},
    ]


def test_a_job_without_a_pipeline_has_no_stages(api):
    api["answers"]["/c/acme/offers/1"] = {"offer": {}}

    assert asyncio.run(recruitee.stages("acme", "token", "1")) == []


def test_a_job_is_its_title_description_and_requirements(api):
    api["answers"]["/c/acme/offers/1"] = {
        "offer": {"title": "Accountant", "description": "<p>Join</p>", "requirements": None}
    }

    assert asyncio.run(recruitee.job("acme", "token", "1")) == {
        "name": "Accountant",
        "sections": ["<p>Join</p>", ""],
    }


def test_a_note_goes_on_the_candidate_as_the_tokens_person(api):
    asyncio.run(recruitee.comment("acme", "token", "44", None, "Grade: 82%"))

    [note] = api["requests"]
    assert (note.method, str(note.url)) == ("POST", API + "/candidates/44/notes")
    assert json.loads(note.content) == {
        "note": {"body": "Grade: 82%", "visibility": {"level": "public"}}
    }


def test_a_candidate_gone_from_recruitee_is_a_404_not_a_rejected_key(api):
    api["answers"]["/c/acme/candidates/44/notes"] = 404

    with pytest.raises(HTTPException) as failed:
        asyncio.run(recruitee.comment("acme", "token", "44", None, "Grade: 82%"))

    assert failed.value.status_code == 404


def signature(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_only_bodies_signed_with_the_web_hooks_secret_count():
    body = b'{"event_type": "candidate_moved"}'
    given = signature("secret", body)

    assert recruitee_signed("secret", body, given)
    assert recruitee_signed("secret", body, f" {given.upper()}\n")
    assert not recruitee_signed("other", body, given)
    assert not recruitee_signed("secret", body + b" ", given)
    assert not recruitee_signed("secret", body, "")


def test_recruitee_has_its_client():
    assert ats_clients.client("recruitee") is recruitee
    assert recruitee.KEYS == ("company", "token")
