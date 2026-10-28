"""What site sends the assistant's help chat to answer from (GET /internal/help/knowledge),
and the help chat's old addresses, which send the browser to the assistant."""

import asyncio

from prepza_common.auth.service_auth import issue_token
from prepza_common.limits.limit_list import LIMITS

from site_content.helpers.help import knowledge
from site_content.helpers.page_guides import GUIDES
from site_content.services.help import guide_limits
from tests.unit.api.v1.test_help import CATALOG, fake_catalog

SECRET = "test-secret-that-is-at-least-32-bytes"
FROM_ASSISTANT = {"Authorization": "Bearer " + issue_token("assistant", "site", SECRET)}
URL = "/internal/help/knowledge"


def test_the_help_chat_reads_the_platform_guide_in_english_with_the_visitors_prices(
    client, monkeypatch, redis
):
    asked = []
    monkeypatch.setattr("site_content.services.help.billing.catalog", fake_catalog(CATALOG, asked))

    response = client.get(URL, params={"country": "DE"}, headers=FROM_ASSISTANT)
    found = response.json()

    assert response.status_code == 200
    assert asked == ["DE"]
    assert found["page_guide"] is None
    # The text Mira reads too (GET /help/guide), in English whatever the page's language.
    limits = asyncio.run(guide_limits(redis))
    assert found["knowledge"] == knowledge("en", CATALOG, limits)
    assert f"can own up to {LIMITS['MAX_OWNED_COMPANIES'].default}" in found["knowledge"]
    assert "Refunds: you can ask for a refund" in found["knowledge"]
    assert "Who is responsible" in found["knowledge"]
    assert '"candidate_credits": 500' in found["knowledge"]
    assert "secret-token" not in found["knowledge"]


def test_the_guide_of_the_page_asked_on_comes_in_english_and_an_unknown_page_has_none(
    client, monkeypatch
):
    monkeypatch.setattr("site_content.services.help.billing.catalog", fake_catalog(CATALOG))
    guide = GUIDES["en"]["pricing"]

    pricing = client.get(URL, params={"page": "pricing"}, headers=FROM_ASSISTANT).json()
    unknown = client.get(URL, params={"page": "superadmin"}, headers=FROM_ASSISTANT).json()

    assert pricing["page_guide"].startswith(guide["title"])
    assert all(item in pricing["page_guide"] for item in guide["actions"] + guide["tips"])
    assert unknown["page_guide"] is None
    assert client.get(URL, params={"page": "x" * 100}, headers=FROM_ASSISTANT).status_code == 422


def test_only_another_service_reads_the_help_chats_knowledge(client):
    assert client.get(URL).status_code == 401
