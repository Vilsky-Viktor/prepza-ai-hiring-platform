import asyncio

import httpx
import pytest

from app.config.settings import settings
from app.integrations import resend


def unsuppress(monkeypatch, status_code: int) -> list[httpx.Request]:
    """Takes an address off a Resend that answers `status_code`; the requests it got."""
    requests = []

    def answer(request):
        requests.append(request)

        return httpx.Response(status_code, json={"deleted": True})

    client = httpx.AsyncClient(transport=httpx.MockTransport(answer))
    monkeypatch.setattr(resend.http, "get_client", lambda: client)
    monkeypatch.setattr(settings, "resend_api_key", "re_test")
    asyncio.run(resend.unsuppress(" Ann+x@Example.com "))

    return requests


@pytest.mark.parametrize("status_code", [200, 404])
def test_an_address_is_taken_off_resends_list_or_was_not_on_it(monkeypatch, status_code):
    [request] = unsuppress(monkeypatch, status_code)

    assert request.method == "DELETE"
    assert request.url.raw_path == b"/suppressions/ann%2Bx@example.com"
    assert request.headers["Authorization"] == "Bearer re_test"


@pytest.mark.parametrize("status_code", [401, 500])
def test_resend_keeping_the_address_is_a_failure(monkeypatch, status_code):
    with pytest.raises(RuntimeError):
        unsuppress(monkeypatch, status_code)
