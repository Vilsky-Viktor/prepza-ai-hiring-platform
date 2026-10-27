import asyncio

import httpx
from prepza_common.http import http

from app.integrations import billing


def test_a_new_accounts_currency_is_asked_for_with_its_country_and_a_failure_is_only_logged(
    monkeypatch,
):
    asked = []

    def answer(request):
        asked.append((request.url.path, dict(request.url.params)))

        return httpx.Response(503)

    client = httpx.AsyncClient(transport=httpx.MockTransport(answer))
    monkeypatch.setattr(http, "get_client", lambda: client)

    asyncio.run(billing.remember_currency("ann", "DE"))
    asyncio.run(billing.remember_currency("ann", None))

    assert asked == [
        ("/internal/users/ann/currency", {"country": "DE"}),
        ("/internal/users/ann/currency", {}),
    ]
