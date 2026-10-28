import asyncio
import uuid

import httpx
import pytest

from assistant.integrations import services
from assistant.models.answers import Answer, Turn
from assistant.models.tools import ToolResult
from assistant.services.show import finish

COMPANY = "8c1d2b8e-1a2b-4c3d-8e9f-0a1b2c3d4e5f"
TURN = Turn(uuid.uuid4(), "ann", uuid.UUID(COMPANY), "t", "en", frozenset({COMPANY}))


@pytest.fixture(autouse=True)
def nothing_named(monkeypatch):
    async def get(service, path, query, token, language, via=None):
        return httpx.Response(404, json={}, request=httpx.Request("GET", "http://x"))

    monkeypatch.setattr(services, "get", get)


def linked(*results: ToolResult, pending: bool = False) -> list[str]:
    answer = Answer()
    answer.results += results
    answer.pending += [uuid.uuid4()] if pending else []
    emitted = []
    asyncio.run(finish(answer, TURN, emitted.append))

    return [link for event in emitted for link in event["block"]["links"]]


def read(name: str) -> ToolResult:
    return ToolResult(name, {"company_id": COMPANY}, 200, {}, None, 0)


@pytest.mark.parametrize(
    ("tool", "page"),
    [
        ("get_auto_top_up", "/top-up"),
        ("get_slack", f"/companies/{COMPANY}/integrations/slack"),
        ("list_ats_connections", f"/companies/{COMPANY}/integrations"),
        ("get_api_settings", f"/companies/{COMPANY}/integrations/api"),
    ],
)
def test_an_answer_about_a_setting_links_its_page_when_the_model_gave_none(tool, page):
    assert linked(read(tool)) == [page]


def test_no_setting_link_beside_a_card_or_for_several_settings():
    assert linked(read("get_auto_top_up"), pending=True) == []
    assert linked(read("get_slack"), read("get_api_settings")) == []


def test_a_failed_read_links_nothing():
    failed = ToolResult("get_slack", {"company_id": COMPANY}, 403, {"error": 403}, None, 0)

    assert linked(failed) == []
