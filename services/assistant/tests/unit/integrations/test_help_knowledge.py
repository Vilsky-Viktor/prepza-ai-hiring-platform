import asyncio

import httpx
from prepza_common.auth.service_auth import token_caller

from assistant.integrations import help_knowledge as module
from assistant.schemas.help_chat import HelpKnowledge

SECRET = "test-secret-that-is-at-least-32-bytes"


def test_the_knowledge_is_asked_of_site_as_the_assistant_with_the_country_and_page(
    monkeypatch,
):
    asked = []

    def answer(request: httpx.Request) -> httpx.Response:
        asked.append(request)

        return httpx.Response(200, json={"knowledge": "guide", "page_guide": "pricing"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(answer))
    monkeypatch.setenv("SITE_SERVICE_SECRET", SECRET)
    monkeypatch.setattr(module.http, "get_client", lambda: client)

    found = asyncio.run(module.help_knowledge("DE", "pricing"))
    without = asyncio.run(module.help_knowledge(None, None))

    assert found == HelpKnowledge(knowledge="guide", page_guide="pricing")
    assert without.knowledge == "guide"
    assert str(asked[0].url) == "http://site/internal/help/knowledge?country=DE&page=pricing"
    assert str(asked[1].url) == "http://site/internal/help/knowledge"
    token = asked[0].headers["Authorization"].removeprefix("Bearer ")
    assert token_caller(token, SECRET, "site") == "assistant"
