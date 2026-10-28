from prepza_common.limits.limit_list import LIMITS

from rounds.constants.terms import TERMS_SECTIONS

CATALOG = {
    "environment": "sandbox",
    "client_token": "secret-token",
    "currency": "USD",
    "candidate_credits": 500,
    "candidate_cents_min": 200,
    "candidate_cents_max": 500,
    "welcome_company": 1500,
}
MAX_COMPANIES = LIMITS["MAX_OWNED_COMPANIES"].default


def fake_catalog(catalog, asked=None):
    """Billing's catalog in each country's currency; the countries asked for go in `asked`."""

    async def get(country=None):
        if asked is not None:
            asked.append(country)

        return catalog

    return get


def test_legal_documents_are_served(client):
    terms = client.get("/help/legal/terms").json()

    assert [section["heading"] for section in terms["sections"]] == [
        section["heading"] for section in TERMS_SECTIONS
    ]
    assert client.get("/help/legal/privacy").status_code == 200
    assert client.get("/help/legal/cookies").status_code == 422


def test_billings_prices_are_kept_for_a_while(monkeypatch):
    import asyncio

    import httpx
    from prepza_common.redis import memory_cache

    from rounds.integrations import billing

    calls = []

    class FakeClient:
        async def get(self, url, params=None):
            calls.append(params)

            return httpx.Response(200, json=CATALOG, request=httpx.Request("GET", url))

    monkeypatch.setattr(memory_cache, "_entries", {})
    monkeypatch.setattr("rounds.integrations.billing.http.get_client", lambda: FakeClient())

    # Kept per country, as each may have its own currency; none means billing's default.
    for country in (None, None, "DE", "DE"):
        assert asyncio.run(billing.catalog(country)) == CATALOG

    assert calls == [None, {"country": "DE"}]


def test_the_platform_guide_is_served_in_the_pages_language(client, monkeypatch):
    from prepza_common.redis import memory_cache

    from rounds.constants.faq import FAQS

    calls = []

    async def catalog(country=None):
        calls.append(1)

        return CATALOG

    monkeypatch.setattr(memory_cache, "_entries", {})
    monkeypatch.setattr("rounds.services.help.billing.catalog", catalog)

    german = client.get("/help/guide", headers={"Accept-Language": "de"})
    english = client.get("/help/guide")
    client.get("/help/guide", headers={"Accept-Language": "de"})

    assert german.status_code == 200
    assert german.headers["content-type"].startswith("text/plain")
    assert f"Q: {FAQS['de'][0]['question']}" in german.text
    assert f"Q: {FAQS['en'][0]['question']}" in english.text
    assert f"can own up to {MAX_COMPANIES}" in german.text
    assert "secret-token" not in german.text
    # Kept per language: the second German request is built from memory.
    assert len(calls) == 2
