"""get_updates' calls: since when each connection or key is told, what it may read, and how the
MCP server lists and refuses it."""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from prepza_common.i18n.i18n import translate

from assistant.constants.key_tools import KEY_TOOLS
from assistant.constants.mcp import KEY_MISSING_PERMISSION
from assistant.constants.updates import FIRST_CHECK_DAYS, GET_UPDATES, INVALID_SINCE, SETTLE_SECONDS
from assistant.models.answers import Turn
from assistant.services import mcp_tools
from assistant.services import updates as updates_service
from tests.unit.services.test_mcp_keys import key
from tests.unit.services.test_mcp_tools import ACCESS, calls  # noqa: F401 (fixture)

NOW = datetime(2026, 10, 18, 9, tzinfo=UTC)


class Clock(datetime):
    """The time the service reads: NOW, unless a test moves it on."""

    moment = NOW

    @classmethod
    def now(cls, tz=None):
        return cls.moment


@pytest.fixture
def world(monkeypatch):
    """The checks kept per connection, and the updates the services hold, each with when it
    happened and from when it can be read (a step saved in a transaction still open)."""
    checks: dict[str, datetime] = {}
    held: list[tuple[datetime, datetime]] = []
    reads = []

    async def last(connection):
        return checks.get(connection)

    async def save(connection, at):
        checks[connection] = max(at, checks.get(connection, at))

    async def read(arguments, token, language, period, via, site, sees_credits):
        reads.append((period, via, site, sees_credits))
        since, until = period
        found = [happened for happened, readable in held if readable <= Clock.moment]

        return {"items": [happened for happened in found if since < happened <= until]}

    Clock.moment = NOW
    monkeypatch.setattr(updates_service, "datetime", Clock)
    monkeypatch.setattr(updates_service.update_checks, "last", last)
    monkeypatch.setattr(updates_service.update_checks, "save", save)
    monkeypatch.setattr(updates_service, "read", read)

    return checks, held, reads


def check(access=ACCESS, **arguments):
    result = asyncio.run(updates_service.for_app(arguments, access, "token", "de"))

    return result.status_code, result.content


def told(access=ACCESS, **arguments) -> list[datetime]:
    status, content = check(access, **arguments)

    assert status == 200

    return content["data"]["items"]


def test_the_first_check_covers_the_last_days_up_to_a_moment_ago(world):
    checks, _, reads = world

    check()

    settled = NOW - timedelta(seconds=SETTLE_SECONDS)
    assert reads[0][0] == (settled - timedelta(days=FIRST_CHECK_DAYS), settled)
    assert checks == {ACCESS.grant_id: settled}


def test_each_update_reaches_a_connection_once(world):
    _, held, _ = world
    happened = NOW - timedelta(minutes=5)
    held.append((happened, happened))

    first = told()
    Clock.moment = NOW + timedelta(hours=1)
    second = told()

    assert (first, second) == ([happened], [])


def test_a_step_landing_during_a_check_reaches_the_next_one(world):
    _, held, _ = world
    # Stamped 10 seconds before the check but committed only after it.
    happened = NOW - timedelta(seconds=10)
    held.append((happened, NOW + timedelta(seconds=1)))

    first = told()
    Clock.moment = NOW + timedelta(minutes=10)
    second = told()
    Clock.moment = NOW + timedelta(minutes=20)
    third = told()

    assert (first, second, third) == ([], [happened], [])


def test_two_connections_each_get_an_update_once(world):
    _, held, _ = world
    happened = NOW - timedelta(minutes=5)
    held.append((happened, happened))
    other = ACCESS.model_copy(update={"grant_id": "another-connection"})

    first = [told(), told(other)]
    Clock.moment = NOW + timedelta(hours=1)
    second = [told(), told(other)]

    assert first == [[happened], [happened]]
    assert second == [[], []]


def test_an_api_key_keeps_its_own_check(world):
    checks, held, _ = world
    happened = NOW - timedelta(minutes=5)
    held.append((happened, happened))

    by_app = told()
    by_key = told(key("candidates:read"))

    assert (by_app, by_key) == ([happened], [happened])
    assert set(checks) == {ACCESS.grant_id, key().key_id}


def test_since_asks_for_a_period_and_doesnt_count_as_a_check(world):
    checks, held, reads = world
    happened = NOW - timedelta(days=20)
    held.append((happened, happened))

    asked = told(since="2026-09-01T00:00:00Z")
    after = told()

    settled = NOW - timedelta(seconds=SETTLE_SECONDS)
    assert reads[0][0] == (datetime(2026, 9, 1, tzinfo=UTC), settled)
    assert (asked, after) == ([happened], [])
    assert checks == {ACCESS.grant_id: settled}


def test_a_since_that_isnt_a_time_is_refused_in_the_users_language(world):
    checks, _, reads = world

    status, content = check(since="last week")

    assert (status, content) == (422, {"error": 422, "detail": translate(INVALID_SINCE, "de")})
    assert translate(INVALID_SINCE, "en") == (
        "since must be an ISO 8601 time, like 2026-10-01T09:00:00Z."
    )
    assert reads == [] and checks == {}


@pytest.mark.parametrize(
    "access, sees_credits",
    [
        (ACCESS, True),
        (key("candidates:read"), False),
        (key("candidates:read", "credits:read"), True),
    ],
)
def test_credits_only_for_an_app_or_a_key_that_may_read_them(world, access, sees_credits):
    _, _, reads = world

    check(access)

    assert (reads[0][1], reads[0][3]) == ("mcp", sees_credits)


def test_the_panel_reads_the_last_days_with_the_apps_own_links_and_keeps_no_check(world):
    checks, _, reads = world
    turn = Turn(uuid4(), "ann", None, "token", "de")

    result = asyncio.run(updates_service.in_panel({}, turn))

    assert result.status_code == 200
    assert reads[0] == ((NOW - timedelta(days=FIRST_CHECK_DAYS), NOW), "assistant", "", True)
    assert checks == {}


def test_the_mcp_server_lists_it_as_a_read_needing_candidates_read():
    listed = {tool.name: tool for tool in mcp_tools.listed()}
    refused = {tool.name for tool in mcp_tools.listed(key("credits:read"))}

    assert listed[GET_UPDATES].annotations.read_only_hint is True
    assert "since" in listed[GET_UPDATES].input_schema["properties"]
    assert KEY_TOOLS[GET_UPDATES] == "candidates:read"
    assert GET_UPDATES not in refused


def test_a_key_without_candidates_read_is_refused_before_anything_is_called(calls):  # noqa: F811
    result = asyncio.run(mcp_tools.call(GET_UPDATES, {}, key("credits:read")))
    missing = KEY_MISSING_PERMISSION.format(permission="candidates:read")

    assert (result.is_error, json.loads(result.content[0].text)) == (True, {"error": missing})
    assert calls == []


def test_an_invalid_since_through_mcp_is_an_error_result_with_its_reason(calls, world):  # noqa: F811
    result = asyncio.run(mcp_tools.call(GET_UPDATES, {"since": "soon"}, ACCESS))

    assert result.is_error
    assert json.loads(result.content[0].text) == {"error": translate(INVALID_SINCE, "de")}
