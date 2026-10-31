import asyncio
import json

import httpx
import pytest
from fastapi import HTTPException
from testee_common.auth.key_actor import key_actor
from testee_common.auth.service_auth import token_claims
from testee_common.http import http
from testee_common.i18n.i18n import translate

from assistant.constants.chat import OTHER_COMPANY
from assistant.constants.key_tools import KEY_TOOLS
from assistant.constants.mcp import KEY_MISSING_PERMISSION
from assistant.constants.tool_calls import UNKNOWN_TOOL
from assistant.integrations import api_keys, firebase_tokens, services
from assistant.integrations.services import KEY_CLAIMS
from assistant.models.oauth_tokens import Access
from assistant.services import mcp_tools
from assistant.services.oauth_provider import Provider
from assistant.services.registry import tools
from tests.unit.services.test_mcp_tools import COMPANY, calls  # noqa: F401 (fixture)

SECRET = "test-secret-that-is-at-least-32-bytes"
KEY_ID = "5b0f6a3e-2c1d-4e8f-9a0b-1c2d3e4f5a6b"
OTHER = "00000000-0000-4000-8000-000000000099"


def key(*permissions: str) -> Access:
    return Access(
        token="te_x",
        client_id=KEY_ID,
        scopes=["testee"],
        subject=key_actor(KEY_ID),
        client_name="API key",
        key_id=KEY_ID,
        company_id=COMPANY,
        permissions=["mcp", *permissions],
    )


def verified(monkeypatch, permissions):
    async def verify(raw, ip):
        if permissions is None:
            return None

        return {
            "id": KEY_ID,
            "company_id": COMPANY,
            "permissions": permissions,
        }

    monkeypatch.setattr(api_keys, "verify", verify)


def called(name: str, arguments: dict, access: Access) -> tuple[bool, dict]:
    result = asyncio.run(mcp_tools.call(name, arguments, access))

    return result.is_error, json.loads(result.content[0].text)


def test_every_key_tool_is_a_tool_an_app_may_call():
    listed = {tool.name for tool in mcp_tools.listed()}

    assert set(KEY_TOOLS) <= listed


def test_a_key_with_mcp_signs_in_as_itself_in_its_company(monkeypatch):
    verified(monkeypatch, ["candidates:read", "mcp"])

    access = asyncio.run(Provider().load_access_token("te_key"))

    assert (access.subject, access.company_id, access.key_id) == (
        key_actor(KEY_ID),
        COMPANY,
        KEY_ID,
    )
    assert access.permissions == ["candidates:read", "mcp"]


@pytest.mark.parametrize("permissions", [["interviews:read", "candidates:read"], None])
def test_a_key_without_mcp_or_that_doesnt_work_is_refused(monkeypatch, permissions):
    verified(monkeypatch, permissions)

    assert asyncio.run(Provider().load_access_token("te_key")) is None


def test_a_key_lists_only_what_its_permissions_allow():
    names = {tool.name for tool in mcp_tools.listed(key("candidates:read"))}

    assert names == {
        name for name, needs in KEY_TOOLS.items() if needs in ("mcp", "candidates:read")
    }
    # The account, the team and settings never.
    assert not names & {"get_me", "update_language", "list_members", "rename_company"}


@pytest.mark.parametrize(
    ("permission", "notes_tools"),
    [
        ("notes:read", {"list_interview_notes"}),
        ("notes:add", {"list_interview_notes", "add_interview_note"}),
    ],
)
def test_a_keys_notes_permission_lists_the_notes_tools_but_never_pinning(permission, notes_tools):
    # The api gives a key notes:add with the notes:read it implies.
    granted = ["notes:read", permission]
    names = {tool.name for tool in mcp_tools.listed(key(*granted))}

    assert {name for name in names if "note" in name} == notes_tools
    assert "pin_interview_note" not in KEY_TOOLS


def test_a_key_is_refused_a_tool_its_permissions_dont_allow(calls):  # noqa: F811
    access = key("candidates:read")
    missing = KEY_MISSING_PERMISSION.format(permission="candidates:invite")

    invite = called("invite_candidate", {"interview_id": COMPANY, "email": "a@b.co"}, access)
    account = called("get_me", {}, access)

    assert invite == (True, {"error": missing})
    assert account == (True, {"error": UNKNOWN_TOOL})
    assert calls == []


def test_a_key_is_refused_another_company_before_anything_is_called(calls):  # noqa: F811
    error, content = called("get_company", {"company_id": OTHER}, key())

    # A key is no person: in English.
    assert (error, content) == (True, {"error": translate(OTHER_COMPANY, "en")})
    assert calls == []


def test_a_keys_calls_act_as_the_key_never_signing_anyone_in(calls, monkeypatch):  # noqa: F811
    """Its maker's account plays no part: gone or not, the key calls as itself."""

    async def no_sign_in(uid):
        raise AssertionError("a key signs no one in")

    monkeypatch.setattr(firebase_tokens, "sign_in", no_sign_in)

    error, _ = called("get_company", {"company_id": COMPANY}, key())

    assert not error
    # No person's token: each call's own is signed for its service (integrations/services.py).
    assert [(item[3], item[4]) for item in calls] == [("", "en")]


def test_a_keys_calls_carry_its_company_and_id_to_companies(calls, monkeypatch):  # noqa: F811
    claims = []
    get = services.get

    async def noting(*args, **kwargs):
        claims.append(KEY_CLAIMS.get())

        return await get(*args, **kwargs)

    monkeypatch.setattr(services, "get", noting)

    error, _ = called("get_company", {"company_id": COMPANY}, key())

    assert not error
    assert claims == [{"company": COMPANY, "key": KEY_ID}]


def test_a_keys_call_is_signed_as_the_key_and_companies_header_carries_its_company(monkeypatch):
    sent = []

    class Client:
        async def request(self, method, url, params, json, headers, timeout):
            sent.append(headers)

            return httpx.Response(200, json={})

    monkeypatch.setattr(http, "get_client", Client)

    async def as_key():
        KEY_CLAIMS.set({"company": COMPANY, "key": KEY_ID})
        await services.get("companies", "/pause", {}, "token", "en", via="mcp")

    async def as_key_to_library():
        KEY_CLAIMS.set({"company": COMPANY, "key": KEY_ID})
        await services.get("library", "/templates", {}, "", "en", via="mcp")

    asyncio.run(as_key())
    asyncio.run(as_key_to_library())
    claims = token_claims(sent[0]["X-Assistant"], SECRET, "companies")
    signed = token_claims(sent[0]["Authorization"][7:], SECRET, "companies")
    to_library = token_claims(sent[1]["Authorization"][7:], SECRET, "library")

    assert (claims["iss"], claims["company"], claims["key"]) == ("mcp", COMPANY, KEY_ID)
    # The call itself is the key's, signed for the service it goes to; never a person's token.
    assert (signed["iss"], signed["key"]) == ("mcp", KEY_ID)
    assert (to_library["iss"], to_library["key"]) == ("mcp", KEY_ID)


def test_the_docs_list_the_tools_and_limits_an_app_meets(client):
    response = client.get("/mcp/tools")
    body = response.json()
    by_name = {tool["name"]: tool for tool in body["tools"]}

    assert response.status_code == 200
    assert set(by_name) == {tool.name for tool in mcp_tools.listed()}
    assert by_name["revoke_candidate"]["destructive"] is True
    assert by_name["get_company"]["read_only"] is True
    assert by_name["invite_candidate"]["key_permission"] == "candidates:invite"
    assert by_name["update_language"]["key_permission"] is None
    assert body["limits"] == {"calls_per_minute": 60, "calls_per_day": 3000, "writes_per_hour": 30}
    assert "delete_company" in tools() and "delete_company" not in by_name


@pytest.mark.parametrize(("status", "expected"), [(401, None), (200, {"id": KEY_ID})])
def test_the_api_answers_whether_a_key_works(monkeypatch, status, expected):
    class Client:
        async def post(self, url, json, headers):
            assert url == "http://api/internal/keys/verify"
            assert json == {"key": "te_key", "ip": "203.0.113.7"}
            assert token_claims(headers["Authorization"][7:], SECRET, "api")["iss"] == "assistant"

            request = httpx.Request("POST", url)

            return httpx.Response(
                status, json=expected or {"detail": "Invalid API key"}, request=request
            )

    monkeypatch.setattr(http, "get_client", Client)

    assert asyncio.run(api_keys.verify("te_key", "203.0.113.7")) == expected


def test_over_the_companys_api_limit_a_key_gets_a_429(monkeypatch):
    class Client:
        async def post(self, url, json, headers):
            return httpx.Response(
                429,
                json={"detail": "Too many requests"},
                headers={"Retry-After": "17"},
                request=httpx.Request("POST", url),
            )

    monkeypatch.setattr(http, "get_client", Client)

    with pytest.raises(HTTPException) as refused:
        asyncio.run(api_keys.verify("te_key", None))

    assert (refused.value.status_code, refused.value.detail) == (429, "Too many requests")
    assert refused.value.headers == {"Retry-After": "17"}


def test_a_keys_use_counts_in_the_funnel_as_an_api_key(monkeypatch, redis):
    tracked = []

    async def track(event, **fields):
        tracked.append((event, fields))

    monkeypatch.setattr(mcp_tools, "track", track)
    monkeypatch.setattr(mcp_tools, "get_redis", lambda: redis)

    asyncio.run(mcp_tools.mark_active(key()))

    assert tracked == [("mcp_active", {"user_id": key_actor(KEY_ID), "client": "api_key"})]
