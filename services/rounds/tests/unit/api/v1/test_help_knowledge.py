"""What rounds sends the assistant's help chat to answer from (GET /internal/help/knowledge),
and the help chat's old addresses, which send the browser to the assistant."""

import asyncio
import uuid

from prepza_common.auth.service_auth import issue_token
from prepza_common.limits.limit_list import LIMITS

from rounds.helpers.help import knowledge
from rounds.helpers.page_guides import GUIDES
from rounds.services.help import guide_limits
from tests.unit.api.v1.test_help import CATALOG, fake_catalog

SECRET = "test-secret-that-is-at-least-32-bytes"
FROM_ASSISTANT = {"Authorization": "Bearer " + issue_token("assistant", "rounds", SECRET)}
URL = "/internal/help/knowledge"


def test_the_help_chat_reads_the_platform_guide_in_english_with_the_visitors_prices(
    client, monkeypatch, redis
):
    asked = []
    monkeypatch.setattr("rounds.services.help.billing.catalog", fake_catalog(CATALOG, asked))

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
    monkeypatch.setattr("rounds.services.help.billing.catalog", fake_catalog(CATALOG))
    guide = GUIDES["en"]["pricing"]

    pricing = client.get(URL, params={"page": "pricing"}, headers=FROM_ASSISTANT).json()
    unknown = client.get(URL, params={"page": "superadmin"}, headers=FROM_ASSISTANT).json()

    assert pricing["page_guide"].startswith(guide["title"])
    assert all(item in pricing["page_guide"] for item in guide["actions"] + guide["tips"])
    assert unknown["page_guide"] is None
    assert client.get(URL, params={"page": "x" * 100}, headers=FROM_ASSISTANT).status_code == 422


def test_only_another_service_reads_the_help_chats_knowledge(client):
    assert client.get(URL).status_code == 401


def test_the_old_help_chat_and_vote_addresses_send_the_browser_to_the_assistant(client):
    answer = uuid.uuid4()

    chat = client.post("/help/chat", json={}, follow_redirects=False)
    vote = client.put(f"/help/answers/{answer}/vote", json={}, follow_redirects=False)

    # 307 keeps the method and the body, so the browser asks the assistant the same.
    assert (chat.status_code, chat.headers["location"]) == (307, "/api/assistant/help/chat")
    assert (vote.status_code, vote.headers["location"]) == (
        307,
        f"/api/assistant/help/answers/{answer}/vote",
    )
