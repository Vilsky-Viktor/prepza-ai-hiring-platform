import asyncio
import uuid

import httpx
import pytest

from assistant.constants.key_tools import KEY_TOOLS
from assistant.integrations import services
from assistant.models.answers import Turn
from assistant.services import mcp_tools
from assistant.services.registry import tools
from assistant.services.show import show
from assistant.services.tool_calls import call_tool

TURN = Turn(uuid.uuid4(), "ann", None, "t", "de", frozenset())
ARTICLE = {
    "slug": "hire-testers",
    "title": "Tester einstellen",
    "updated": "2026-10-02",
    "body": "Beginne mit der Rolle.",
    "description": "Ein Prozess.",
    "language": "de",
    "path": "/guides/hire-testers",
}


@pytest.fixture
def site(monkeypatch):
    """Rounds answering with one guide; what was asked, as (service, path, language)."""
    asked = []

    async def get(service, path, query, token, language, via=None):
        asked.append((service, path, language))
        request = httpx.Request("GET", "http://site")

        if path == "/help/guides/hire-testers":
            return httpx.Response(200, json=ARTICLE, request=request)

        if path == "/help/guides":
            listed = {key: value for key, value in ARTICLE.items() if key != "body"}

            return httpx.Response(200, json=[listed], request=request)

        return httpx.Response(404, json={"detail": "There's no such guide."}, request=request)

    monkeypatch.setattr(services, "get", get)

    return asked


def test_the_guides_are_listed_and_read_from_site_in_the_users_language(site):
    listed = asyncio.run(call_tool("list_guides", {}, "user-token", "de", None))
    read = asyncio.run(call_tool("get_guide", {"slug": "hire-testers"}, "user-token", "de", None))

    assert site == [
        ("site", "/help/guides", "de"),
        ("site", "/help/guides/hire-testers", "de"),
    ]
    assert listed.content["data"] == [
        {"slug": "hire-testers", "title": "Tester einstellen", "description": "Ein Prozess."}
    ]
    assert read.content["data"] == {
        "slug": "hire-testers",
        "title": "Tester einstellen",
        "updated": "2026-10-02",
        "body": "Beginne mit der Rolle.",
    }
    assert not tools()["get_guide"].confirm and not tools()["list_guides"].confirm


def test_a_guide_link_opens_the_guides_page_named_by_its_title(site):
    content, block = asyncio.run(
        show({"kind": "link", "page": "guide", "slug": "hire-testers"}, TURN, set())
    )

    assert content == {"detail": "Shown under your answer."}
    assert block["links"] == ["/guides/hire-testers"]
    assert block["label"] == "Tester einstellen"
    assert ("site", "/help/guides/hire-testers", "de") in site


@pytest.mark.parametrize("slug", ["missing", "../faq", None])
def test_no_link_is_shown_to_a_guide_that_isnt_there(site, slug):
    content, block = asyncio.run(show({"kind": "link", "page": "guide", "slug": slug}, TURN, set()))

    assert block is None
    assert content["error"] == 404


def test_ai_apps_and_api_keys_with_mcp_get_the_guides():
    names = {tool.name for tool in mcp_tools.listed()}

    assert {"list_guides", "get_guide"} <= names
    assert KEY_TOOLS["list_guides"] == KEY_TOOLS["get_guide"] == "mcp"
