import time
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import pytest
from prepza_common.auth.auth import current_user
from prepza_common.auth.tokens import hashed
from prepza_common.auth.user import User

from app.constants.mcp import CONNECT_COOKIE, OTHER_BROWSER
from app.helpers.mcp_clients import describe_client
from app.main import app
from app.services import connections
from app.storage import oauth, oauth_requests

ANN = User(uid="ann", email="ann@example.com", email_verified=True)
REQUEST = {
    "client_id": "c1",
    "client_name": "Claude",
    "redirect_host": "claude.ai",
    "known_client": True,
    "redirect_uri": "https://claude.ai/api/mcp/auth_callback",
    "redirect_uri_provided_explicitly": True,
    "code_challenge": "challenge",
    "state": "s1",
    "scopes": ["prepza"],
}


@pytest.fixture
def kept(monkeypatch):
    """A signed-in user, a waiting request, and the codes and connections, in memory."""
    store = SimpleNamespace(requests={"r1": dict(REQUEST)}, codes={}, grants={}, tracked=[])

    async def peek_request(request_id):
        return store.requests.get(request_id)

    async def take_request(request_id):
        return store.requests.pop(request_id, None)

    async def save_code(code_hash, code):
        store.codes[code_hash] = code

    async def of_user(user_id):
        return [grant for grant in store.grants.values() if grant.user_id == user_id]

    async def remove(grant_id, user_id=None):
        grant = store.grants.get(grant_id)

        if grant is None or grant.user_id != user_id:
            return None

        return store.grants.pop(grant_id)

    async def nothing(*args, **kwargs):
        store.tracked.append(args[0] if args else None)

    monkeypatch.setattr(oauth_requests, "peek_request", peek_request)
    monkeypatch.setattr(oauth_requests, "take_request", take_request)
    monkeypatch.setattr(oauth_requests, "save_code", save_code)
    monkeypatch.setattr(oauth, "of_user", of_user)
    monkeypatch.setattr(oauth, "remove", remove)
    monkeypatch.setattr(connections, "hit_or_skip", nothing)
    monkeypatch.setattr(connections, "track", nothing)
    app.dependency_overrides[current_user] = lambda: ANN

    yield store

    app.dependency_overrides.clear()


def grant(user_id: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        user_id=user_id,
        client_name="ChatGPT",
        redirect_host="chatgpt.com",
        created_at=datetime(2026, 10, 1, tzinfo=UTC),
        last_used_at=None,
        scope="prepza",
    )


def test_the_consent_page_reads_what_the_app_asks(client, kept):
    response = client.get("/connect/r1")

    assert response.json() == {
        "client_name": "Claude",
        "redirect_host": "claude.ai",
        "known_client": True,
        "read_only": False,
    }
    assert client.get("/connect/gone").status_code == 404


def test_allowing_gives_the_app_a_code_bound_to_the_user_once(client, kept):
    # The browser that asked to connect (its /authorize answer marked it).
    client.cookies.set(CONNECT_COOKIE, "r1")
    response = client.post("/connect/r1/approve")

    url = urlparse(response.json()["redirect_url"])
    query = parse_qs(url.query)
    assert f"{url.scheme}://{url.netloc}{url.path}" == REQUEST["redirect_uri"]
    assert query["state"] == ["s1"]
    # The answer names who gave it (RFC 9207).
    assert query["iss"] == ["http://localhost:8090"]
    code = kept.codes[hashed(query["code"][0])]
    assert code["user_id"] == "ann" and code["client_id"] == "c1"
    assert code["expires_at"] > time.time()
    # The request is answered: a second answer finds nothing.
    assert client.post("/connect/r1/approve").status_code == 404
    assert client.post("/connect/r1/deny").status_code == 404


@pytest.mark.parametrize("marked", [None, "another-request"])
def test_a_consent_link_opened_in_another_browser_connects_nothing(client, kept, marked):
    """Someone started connecting their own app and sent the link: allowing or refusing it is
    refused, and the request stays for the browser that started it."""
    client.cookies.clear()

    if marked:
        client.cookies.set(CONNECT_COOKIE, marked)

    response = client.post("/connect/r1/approve")
    denied = client.post("/connect/r1/deny")

    assert (response.status_code, denied.status_code) == (403, 403)
    assert response.json()["detail"] == denied.json()["detail"] == OTHER_BROWSER
    assert kept.codes == {}
    # Neither answer ends it: it stays for its own browser.
    assert client.get("/connect/r1").status_code == 200


@pytest.mark.parametrize(
    ("asked", "body", "scope"),
    [
        (["prepza"], None, "prepza"),
        (["prepza"], {"read_only": True}, "prepza:read"),
        (["prepza:read"], None, "prepza:read"),
        # An app that asked only to read can't be given more.
        (["prepza:read"], {"read_only": False}, "prepza:read"),
    ],
)
def test_the_code_carries_what_the_user_allowed(client, kept, asked, body, scope):
    kept.requests["r1"]["scopes"] = asked
    client.cookies.set(CONNECT_COOKIE, "r1")

    assert client.get("/connect/r1").json()["read_only"] is (asked == ["prepza:read"])

    response = client.post("/connect/r1/approve", json=body)

    code = parse_qs(urlparse(response.json()["redirect_url"]).query)["code"][0]
    assert kept.codes[hashed(code)]["scopes"] == [scope]


def test_denying_tells_the_app_and_gives_no_code(client, kept):
    client.cookies.set(CONNECT_COOKIE, "r1")
    response = client.post("/connect/r1/deny")

    query = parse_qs(urlparse(response.json()["redirect_url"]).query)
    assert query == {
        "error": ["access_denied"],
        "state": ["s1"],
        "iss": ["http://localhost:8090"],
    }
    assert kept.codes == {}


def test_viewing_and_refusing_a_request_are_counted_per_address(client, kept, monkeypatch):
    counted = []

    async def hit(redis, key, name, **whose):
        counted.append((key, name, whose["user_id"]))

    monkeypatch.setattr(connections, "hit_or_skip", hit)
    client.cookies.set(CONNECT_COOKIE, "r1")

    client.get("/connect/r1")
    client.post("/connect/r1/deny")

    assert counted == [
        ("rate:assistant:mcp:consent:testclient", "AUTHORIZATIONS_PER_IP_HOUR", "ann"),
        ("rate:assistant:mcp:deny:testclient", "AUTHORIZATIONS_PER_IP_HOUR", "ann"),
    ]


def test_the_user_lists_and_disconnects_only_their_own_apps(client, kept):
    mine, theirs = grant("ann"), grant("bob")
    kept.grants = {mine.id: mine, theirs.id: theirs}

    listed = client.get("/connections").json()

    assert [(item["id"], item["client_name"]) for item in listed] == [(str(mine.id), "ChatGPT")]
    assert client.delete(f"/connections/{theirs.id}").status_code == 404
    assert client.delete(f"/connections/{mine.id}").status_code == 204
    assert list(kept.grants) == [theirs.id]
    assert kept.tracked == ["mcp_disconnected"]


def test_the_consent_routes_need_a_signed_in_user(client):
    assert client.get("/connect/r1").status_code == 401
    assert client.post("/connect/r1/approve").status_code == 401
    assert client.get("/connections").status_code == 401


@pytest.mark.parametrize(
    "name, redirect_uri, expected",
    [
        # A known site names the app, whatever it says it is.
        (
            "Totally Claude",
            "https://claude.ai/api/mcp/auth_callback",
            ("Claude", "claude.ai", True),
        ),
        (
            None,
            "https://chatgpt.com/connector_platform_oauth_redirect",
            ("ChatGPT", "chatgpt.com", True),
        ),
        # An app on the user's own computer, named as it says.
        ("Claude Code", "http://localhost:3118/callback", ("Claude Code", "localhost", True)),
        (None, "http://127.0.0.1:5000/cb", ("Local app", "127.0.0.1", True)),
        # Any other site: unknown, named as it says (or by its site).
        ("Claude", "https://evil.example/cb", ("Claude", "evil.example", False)),
        (" ", "https://other.example/cb", ("other.example", "other.example", False)),
        # Only https is a known site: this one would be labelled Claude otherwise.
        (None, "javascript://claude.ai/%0Aalert(1)", ("claude.ai", "claude.ai", False)),
        (
            None,
            "https://chat.mistral.ai/connections/oauth/callback",
            ("Le Chat", "chat.mistral.ai", True),
        ),
        ("Visual Studio Code", "https://vscode.dev/redirect", ("VS Code", "vscode.dev", True)),
        ("Gemini CLI", "http://localhost:7777/oauth/callback", ("Gemini CLI", "localhost", True)),
        # A known desktop app's own scheme names it.
        ("Anything", "cursor://anysphere.cursor-mcp/oauth", ("Cursor", "cursor://", True)),
        (
            None,
            "vscode://vscode.github-authentication/did-authenticate",
            ("VS Code", "vscode://", True),
        ),
        # Any other scheme: unknown, named as it says.
        ("Zed", "zed://oauth/callback", ("Zed", "oauth", False)),
        # Named after a host too long for a connection: cut to fit.
        (
            None,
            "https://aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.example/cb",
            (
                "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.example",
                False,
            ),
        ),
    ],
)
def test_an_app_is_described_by_the_site_it_returns_to(name, redirect_uri, expected):
    assert describe_client(name, redirect_uri) == expected
