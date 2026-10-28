"""Refused calls of an AI app are logged with ids and the tool's name only, never the token
or the arguments."""

import asyncio
import logging

import pytest
from fastapi import HTTPException
from prepza_common.ai.secrets_check import SECRET_REMOVED
from prepza_common.i18n.i18n import translate

from assistant.integrations import firebase_tokens
from assistant.services import mcp_tools
from tests.unit.services.test_mcp_tools import (  # noqa: F401
    ACCESS,
    COMPANY,
    FAKE_KEY,
    called,
    calls,
)

GRANT = ACCESS.grant_id
# The services as the user (test_mcp_tools.py's fixture): nothing reaches them.
pytestmark = pytest.mark.usefixtures("calls")


@pytest.fixture
def logged(caplog):
    caplog.set_level(logging.INFO, logger=mcp_tools.logger.name)

    return caplog


def lines(caplog) -> list[str]:
    return [record.getMessage() for record in caplog.records if record.name == mcp_tools.__name__]


@pytest.mark.parametrize(
    ("name", "arguments", "why"),
    [
        ("delete_company", {"company_id": COMPANY}, "excluded tool"),
        ("no_such_tool", {"note": "private"}, "unknown tool"),
        ("create_company", {"name": f"Acme {FAKE_KEY}"}, "secret in arguments"),
        ("get_company", {"company_id": "1b2c3d4e-0000-4000-8000-000000000000"}, "not the user"),
    ],
)
def test_a_refused_call_is_logged_with_ids_and_the_tool_only(
    logged, monkeypatch, name, arguments, why
):
    async def own(uid):
        return frozenset({COMPANY})

    monkeypatch.setattr(mcp_tools, "user_companies", own)

    assert called(name, arguments)[0] is True

    [line] = lines(logged)
    assert why in line and name in line and "ann" in line and GRANT in line
    assert ACCESS.token not in line
    assert not any(str(value) in line for value in arguments.values())


def test_a_write_on_a_read_only_connection_is_logged(logged):
    read_only = ACCESS.model_copy(update={"scopes": ["prepza:read"]})
    arguments = {"company_id": COMPANY, "title": "New"}

    result = asyncio.run(mcp_tools.call("rename_company", arguments, read_only))

    [line] = lines(logged)
    assert result.is_error and "read-only connection" in line and "rename_company" in line


def test_a_call_for_an_account_thats_gone_is_logged(logged, monkeypatch):
    async def gone(uid):
        return None

    monkeypatch.setattr(firebase_tokens, "sign_in", gone)

    called("get_me", {})

    [line] = lines(logged)
    assert "account gone" in line and "get_me" in line and "ann" in line


def test_an_unknown_tools_name_is_logged_only_in_part(logged):
    called("x" * 500, {})

    [line] = lines(logged)
    assert "x" * 64 in line and "x" * 65 not in line


@pytest.mark.parametrize(
    "arguments",
    [
        {"tags": ["Backend", f"note {FAKE_KEY}"]},
        {"settings": {"notes": [{"text": f"key {FAKE_KEY}"}]}},
    ],
)
def test_a_secret_deep_in_the_arguments_is_never_sent_on(arguments):
    error, content = called("create_company", {"name": "Acme", **arguments})

    assert (error, content) == (True, {"error": translate(SECRET_REMOVED, "de")})


@pytest.mark.parametrize(
    ("name", "arguments"),
    [
        ("no_such_tool", {}),
        ("delete_company", {"company_id": COMPANY}),
        ("create_company", {"name": f"Acme {FAKE_KEY}"}),
    ],
)
def test_a_refused_call_counts_against_the_users_limit(monkeypatch, name, arguments):
    counted = []

    async def count_call(user_id):
        counted.append(user_id)

    monkeypatch.setattr(mcp_tools, "count_call", count_call)

    assert called(name, arguments)[0] is True
    assert counted == ["ann"]


def test_over_the_limit_a_call_is_refused_before_anything_else(monkeypatch):
    async def over(user_id):
        raise HTTPException(429, "Too many requests. Try again later.")

    monkeypatch.setattr(mcp_tools, "count_call", over)

    error, content = called("no_such_tool", {})

    assert error and content == {"error": translate("Too many requests. Try again later.", "de")}


def test_a_refusal_says_what_to_do_next(monkeypatch):
    other = "1b2c3d4e-0000-4000-8000-000000000000"

    async def own(uid):
        return frozenset({COMPANY})

    monkeypatch.setattr(mcp_tools, "user_companies", own)

    assert called("no_such_tool", {})[1]["error"] == (
        "There is no such tool: use one of the tools listed for you, by its exact name."
    )
    assert called("get_company", {"company_id": other})[1]["error"] == translate(
        "This company isn't one of yours: use a company id from list_companies.", "de"
    )
