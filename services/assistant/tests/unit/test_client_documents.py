import asyncio
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from mcp.shared.auth import InvalidRedirectUriError
from prepza_common import public_urls

from app.constants.limits import MAX_REGISTRATION_BYTES
from app.helpers.mcp_clients import document_client, is_document_id, same_loopback
from app.integrations import client_documents as reader
from app.models.oauth_tokens import Client
from app.services import client_documents
from app.services.oauth_provider import Provider
from app.storage import oauth

URL = "https://app.example.com/oauth/client.json"
DOCUMENT = {
    "client_id": URL,
    "client_name": "Example app",
    "redirect_uris": ["https://app.example.com/callback"],
    "token_endpoint_auth_method": "none",
}


@pytest.mark.parametrize(
    ("client_id", "document"),
    [
        (URL, True),
        ("https://app.example.com/", False),
        ("http://app.example.com/client.json", False),
        ("https://app.example.com/client.json#a", False),
        ("3f0c2b8e-1a2b-4c3d-8e9f-0a1b2c3d4e5f", False),
    ],
)
def test_a_client_id_is_a_metadata_document_only_as_an_https_address_with_a_path(
    client_id, document
):
    assert is_document_id(client_id) is document


def test_a_metadata_document_is_kept_as_a_client_without_a_secret():
    kept = document_client(URL, {**DOCUMENT, "client_secret": "s"})

    assert kept["client_id"] == URL and kept["client_name"] == "Example app"
    assert kept["token_endpoint_auth_method"] == "none"
    assert "client_secret" not in kept


@pytest.mark.parametrize(
    "change",
    [
        {"client_id": "https://other.example.com/client.json"},
        {"token_endpoint_auth_method": "client_secret_post"},
        {"redirect_uris": []},
        {"redirect_uris": ["javascript://app.example.com/%0aalert(1)"]},
        {"redirect_uris": "https://app.example.com/callback"},
    ],
)
def test_a_metadata_document_that_isnt_its_own_or_safe_is_refused(change):
    assert document_client(URL, {**DOCUMENT, **change}) is None


@pytest.mark.parametrize(
    ("given", "same"),
    [
        ("http://127.0.0.1:51234/callback", True),
        ("http://localhost:8080/callback", True),
        ("http://127.0.0.1:51234/other", False),
        ("https://127.0.0.1:51234/callback", False),
        ("http://evil.example.com:51234/callback", False),
    ],
)
def test_an_app_on_the_users_computer_returns_on_any_port(given, same):
    registered = ["http://127.0.0.1/callback", "http://localhost:33418/callback"]

    assert same_loopback(registered, given) is same


def test_the_sdk_takes_a_loopback_return_address_on_another_port():
    client = Client(client_id="c1", redirect_uris=["http://127.0.0.1:33418/callback"])

    assert str(client.validate_redirect_uri("http://127.0.0.1:40000/callback")).endswith(
        ":40000/callback"
    )

    with pytest.raises(InvalidRedirectUriError):
        client.validate_redirect_uri("https://evil.example.com/callback")


@pytest.fixture
def kept(monkeypatch):
    """Kept copies (Postgres) and what the app's site answers, in memory."""
    store = {"copies": {}, "answers": {}, "reads": 0}

    async def read_document(client_id):
        return store["copies"].get(client_id)

    async def keep_document(client_id, info, read_at):
        store["copies"][client_id] = (info, read_at)

    async def read(url):
        store["reads"] += 1

        return store["answers"].get(url)

    monkeypatch.setattr(oauth, "read_document", read_document)
    monkeypatch.setattr(oauth, "keep_document", keep_document)
    monkeypatch.setattr(client_documents.client_documents, "read", read)

    return store


def test_a_metadata_document_is_read_once_a_day(kept):
    kept["answers"][URL] = DOCUMENT

    first = asyncio.run(client_documents.client_of(URL))
    again = asyncio.run(client_documents.client_of(URL))

    assert first == again and first["client_name"] == "Example app"
    assert kept["reads"] == 1

    info, _ = kept["copies"][URL]
    kept["copies"][URL] = (info, datetime.now(UTC) - timedelta(days=2))
    kept["answers"][URL] = {**DOCUMENT, "client_name": "Renamed"}

    assert asyncio.run(client_documents.client_of(URL))["client_name"] == "Renamed"
    assert kept["reads"] == 2


def test_a_site_that_doesnt_answer_leaves_the_kept_copy_in_use(kept):
    old = datetime.now(UTC) - timedelta(days=2)
    kept["copies"][URL] = (document_client(URL, DOCUMENT), old)

    assert asyncio.run(client_documents.client_of(URL))["client_id"] == URL
    assert asyncio.run(client_documents.client_of("https://gone.example.com/c.json")) is None


def test_a_document_that_isnt_valid_any_more_refuses_the_app(kept):
    old = datetime.now(UTC) - timedelta(days=2)
    kept["copies"][URL] = (document_client(URL, DOCUMENT), old)
    kept["answers"][URL] = {**DOCUMENT, "client_id": "https://other.example.com/c.json"}

    assert asyncio.run(client_documents.client_of(URL)) is None


def test_the_provider_reads_a_document_app_and_a_registered_one_from_storage(kept, monkeypatch):
    kept["answers"][URL] = DOCUMENT

    async def get_client(client_id):
        return {"client_id": client_id, "redirect_uris": ["https://claude.ai/cb"]}

    monkeypatch.setattr(oauth, "get_client", get_client)

    assert asyncio.run(Provider().get_client(URL)).client_name == "Example app"
    assert asyncio.run(Provider().get_client("c1")).client_id == "c1"
    assert kept["reads"] == 1


def answering(monkeypatch, response: httpx.Response, address: str | None = "93.184.216.34"):
    """The app's site, answering every request with `response`; requests are recorded."""
    sent = []

    def handler(request):
        sent.append(request)

        return response

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    monkeypatch.setattr(reader, "get_client", lambda: client)
    monkeypatch.setattr(public_urls, "public_address", lambda url: address)

    return sent


def test_a_document_is_read_from_the_checked_address_by_its_hosts_name(monkeypatch):
    sent = answering(monkeypatch, httpx.Response(200, json=DOCUMENT))

    assert asyncio.run(reader.read(URL)) == DOCUMENT
    assert sent[0].url.host == "93.184.216.34"
    assert sent[0].headers["host"] == "app.example.com"


@pytest.mark.parametrize(
    ("response", "address"),
    [
        (httpx.Response(200, json=DOCUMENT), None),
        (httpx.Response(302, headers={"Location": "http://10.0.0.1/"}), "93.184.216.34"),
        (httpx.Response(200, content=b"[1, 2]"), "93.184.216.34"),
        (httpx.Response(200, content=b"not json"), "93.184.216.34"),
        (httpx.Response(200, content=b" " * (MAX_REGISTRATION_BYTES + 1)), "93.184.216.34"),
    ],
)
def test_a_private_redirected_or_bad_document_isnt_read(monkeypatch, response, address):
    sent = answering(monkeypatch, response, address)

    assert asyncio.run(reader.read(URL)) is None
    assert len(sent) <= 1
