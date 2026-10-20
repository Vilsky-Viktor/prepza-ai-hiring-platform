import asyncio
import json

import httpx
import pytest
from fastapi import HTTPException
from prepza_common.i18n import translate
from prepza_common.secrets_check import SECRET_REMOVED
from prepza_common.user import User

from app.constants.actions_flow import NOTHING_TO_CHANGE, SUBJECT_NOT_FOUND
from app.constants.chat import COMPANY_NOT_FOUND
from app.constants.mcp import ACCOUNT_GONE, EXCLUDED_TOOL
from app.constants.mcp_descriptions import MCP_DESCRIPTIONS
from app.constants.tool_calls import UNKNOWN_TOOL
from app.helpers.mcp_schema import mcp_tool
from app.integrations import firebase_tokens, services
from app.models.oauth_tokens import Access
from app.services import mcp_tools
from app.services.registry import tools

COMPANY = "8c1d2b8e-1a2b-4c3d-8e9f-0a1b2c3d4e5f"
ANN = User(uid="ann", email="ann@example.com", email_verified=True, language="de")
ACCESS = Access(
    token="pzm_x",
    client_id="c1",
    scopes=["prepza"],
    subject="ann",
    grant_id="6f1c2b8e-1a2b-4c3d-8e9f-0a1b2c3d4e5f",
    client_name="Claude",
)
FAKE_KEY = "pz_a8Kq3ZpL0vW7tYx2Rn5BdF9hJ4mC6sQe1Ug"


class Calls(list):
    status = 200
    body: object = {"id": COMPANY, "name": "Acme", "role": "owner"}


@pytest.fixture
def calls(monkeypatch):
    """The services as the user: every call with how it came (via) and its idempotency key."""
    made = Calls()

    async def send(
        service,
        method,
        path,
        query,
        body,
        token,
        language,
        idempotency_key=None,
        via=None,
        referral=None,
    ):
        made.append((method, path, body, token, language, idempotency_key, via))
        request = httpx.Request(method, f"http://{service}{path}")

        return httpx.Response(made.status, json=made.body, request=request)

    async def get(service, path, query, token, language, via=None):
        return await send(service, "GET", path, query, None, token, language, via=via)

    async def signed_in(uid):
        return ANN, "id-token"

    async def nothing(*args, **kwargs):
        return True

    monkeypatch.setattr(services, "send", send)
    monkeypatch.setattr(services, "get", get)
    monkeypatch.setattr(firebase_tokens, "sign_in", signed_in)

    for name in ("count_action", "hit_or_skip", "refuse_if_paused", "track", "mark_active"):
        monkeypatch.setattr(mcp_tools, name, nothing)

    return made


def called(name: str, arguments: dict) -> tuple[bool, dict]:
    result = asyncio.run(mcp_tools.call(name, arguments, ACCESS))

    return result.is_error, json.loads(result.content[0].text)


def test_every_tool_but_the_deletions_the_bell_and_the_page_guide_is_listed():
    names = {tool.name for tool in mcp_tools.listed()}
    hidden = {"delete_account", "delete_company", "list_notifications", "get_page_guide"}

    assert names == set(tools()) - hidden


def test_a_tool_is_listed_with_its_parameters_and_hints():
    read = mcp_tool(tools()["get_company"])
    write = mcp_tool(tools()["rename_company"])

    assert read.input_schema == tools()["get_company"].parameters
    assert read.annotations.read_only_hint is True and read.annotations.open_world_hint is False
    # All four hints are set: left out, an app would take a read as destructive.
    assert read.annotations.destructive_hint is False
    assert read.annotations.idempotent_hint is True
    assert write.annotations.read_only_hint is False
    assert write.annotations.destructive_hint is False
    assert write.annotations.idempotent_hint is False


def test_every_listed_tool_has_a_title():
    assert all(tool.title for tool in mcp_tools.listed())


def test_a_result_is_structured_content_and_the_same_as_text(calls):
    result = asyncio.run(mcp_tools.call("get_company", {"company_id": COMPANY}, ACCESS))

    assert result.structured_content["data"]["name"] == "Acme"
    assert json.loads(result.content[0].text) == result.structured_content


def test_a_destructive_write_is_hinted_as_such():
    destructive = [tool for tool in tools().values() if tool.destructive]
    hints = [mcp_tool(tool).annotations for tool in destructive]

    assert hints and all(hint.destructive_hint for hint in hints)


def test_a_read_goes_as_the_user_through_mcp(calls):
    error, content = called("get_company", {"company_id": COMPANY})

    assert not error and content["data"]["name"] == "Acme"
    assert calls == [("GET", f"/companies/{COMPANY}", None, "id-token", "de", None, "mcp")]


def test_a_write_runs_at_once_with_an_idempotency_key_and_absolute_links(calls):
    error, content = called("create_company", {"name": "Acme"})

    assert not error
    (method, path, body, _, _, key, via) = calls[0]
    assert (method, path, body, via) == ("POST", "/companies", {"name": "Acme"}, "mcp")
    assert key
    assert content["links"] == [f"http://localhost:8090/companies/{COMPANY}/interviews"]


def test_the_account_and_company_deletion_are_refused(calls):
    assert called("delete_company", {"company_id": COMPANY}) == (True, {"error": EXCLUDED_TOOL})
    assert called("delete_account", {}) == (True, {"error": EXCLUDED_TOOL})
    # The bell names candidates past the companies that don't allow AI apps.
    assert called("list_notifications", {})[0] is True
    # A page's guide is about the page the user is on in prepza; an app has none.
    assert called("get_page_guide", {"key": "billing"}) == (True, {"error": UNKNOWN_TOOL})
    assert calls == []


def test_a_secret_is_never_sent_on(calls):
    error, content = called("create_company", {"name": f"Acme {FAKE_KEY}"})

    assert (error, content) == (True, {"error": translate(SECRET_REMOVED, "de")})
    assert calls == []


def test_a_subject_that_isnt_the_users_is_refused_before_the_write(calls):
    calls.status = 404

    error, content = called("rename_company", {"company_id": COMPANY, "title": "New"})

    # In the user's language (German here).
    assert error and content == {"error": translate(SUBJECT_NOT_FOUND, "de")}
    assert [call[0] for call in calls] == ["GET"]


def test_a_partial_update_that_changes_nothing_isnt_sent(calls):
    calls.body = {"id": COMPANY, "title": "Acme", "name": "Acme"}

    error, content = called("rename_company", {"company_id": COMPANY, "title": "Acme"})

    assert error and content == {"error": translate(NOTHING_TO_CHANGE, "de")}
    assert [call[0] for call in calls] == ["GET"]


def test_a_services_error_is_an_error_result_with_its_detail(calls):
    calls.status, calls.body = 403, {"detail": "Nur Inhaber"}

    assert called("get_company", {"company_id": COMPANY}) == (True, {"error": "Nur Inhaber"})


def test_a_limit_or_the_pause_is_an_error_result(calls, monkeypatch):
    async def refused(*args, **kwargs):
        raise HTTPException(429, "Too many requests. Try again later.")

    monkeypatch.setattr(mcp_tools, "hit_or_skip", refused)

    error, content = called("get_company", {"company_id": COMPANY})

    assert error and content["error"]
    assert calls == []


def test_an_account_thats_gone_gets_nothing(calls, monkeypatch):
    async def gone(uid):
        return None

    monkeypatch.setattr(firebase_tokens, "sign_in", gone)

    assert called("get_me", {}) == (True, {"error": ACCOUNT_GONE})
    assert calls == []


def test_changing_the_language_drops_the_kept_sign_in(calls, monkeypatch):
    forgotten = []
    monkeypatch.setattr(firebase_tokens, "forget", forgotten.append)
    calls.body = {}

    called("update_language", {"language": "fr"})

    assert forgotten == ["ann"]


def test_a_company_that_isnt_the_users_isnt_called_through_mcp(calls):
    other = "00000000-0000-4000-8000-000000000099"

    error, content = called("get_company", {"company_id": other})

    assert (error, content) == (True, {"error": translate(COMPANY_NOT_FOUND, "de")})
    assert calls == []

def test_an_app_reads_a_fuller_description_where_the_panels_is_short():
    listed = {tool.name: tool.description for tool in mcp_tools.listed()}

    assert listed["get_me"] == MCP_DESCRIPTIONS["get_me"]
    assert tools()["get_me"].definition["function"]["description"] != listed["get_me"]
    # Every fuller description is of a tool that's listed.
    assert set(MCP_DESCRIPTIONS) <= set(listed)
