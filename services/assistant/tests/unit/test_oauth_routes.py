from fastapi import HTTPException
from mcp.shared.auth import OAuthClientInformationFull

from app.models.oauth_tokens import Access
from app.services import oauth_limits, oauth_provider
from app.storage import oauth

SITE = "http://localhost:8090"


def test_the_metadata_names_the_site_as_issuer_and_takes_apps_without_a_secret(client):
    server = client.get("/.well-known/oauth-authorization-server").json()
    resource = client.get("/.well-known/oauth-protected-resource/mcp").json()

    assert server["issuer"] == SITE
    assert server["authorization_endpoint"] == f"{SITE}/authorize"
    assert "none" in server["token_endpoint_auth_methods_supported"]
    assert server["code_challenge_methods_supported"] == ["S256"]
    assert resource == client.get("/.well-known/oauth-protected-resource").json()
    assert resource["resource"] == f"{SITE}/mcp"
    assert resource["authorization_servers"] == [SITE]


def test_the_mcp_endpoint_without_a_token_names_where_to_get_one(client):
    response = client.post("/mcp", json={})

    assert response.status_code == 401
    expected = f'resource_metadata="{SITE}/.well-known/oauth-protected-resource/mcp"'
    assert expected in response.headers["www-authenticate"]


def test_a_browser_app_may_send_every_protocol_revisions_headers(client):
    # 2026-07-28's requests carry Mcp-Method and Mcp-Name; a preflight refusing them would stop
    # browser-based apps (MCP Inspector) at the first call.
    headers = "authorization,content-type,mcp-protocol-version,mcp-method,mcp-name,last-event-id"
    response = client.options(
        "/mcp",
        headers={
            "Origin": "http://localhost:6274",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": headers,
        },
    )

    assert response.status_code == 200
    allowed = response.headers["access-control-allow-headers"].lower()
    assert all(name in allowed for name in headers.split(","))


def test_an_unknown_token_is_refused(client, monkeypatch):
    async def none(access_hash):
        return None

    monkeypatch.setattr(oauth, "by_access", none)

    response = client.post("/mcp", json={}, headers={"Authorization": "Bearer pzm_unknown"})

    assert response.status_code == 401


def test_an_app_registers_without_a_secret_within_the_limits(client, monkeypatch):
    saved, counted = [], []

    async def save_client(client_id, info):
        saved.append(info)

    async def hit(redis, key, name):
        counted.append((key, name))

    monkeypatch.setattr(oauth, "save_client", save_client)
    monkeypatch.setattr(oauth_limits, "hit_or_skip", hit)
    body = {
        "client_name": "Claude Code",
        "redirect_uris": ["http://localhost:3118/callback"],
        "token_endpoint_auth_method": "none",
    }

    response = client.post("/register", json=body)

    assert response.status_code == 201
    assert response.json().get("client_secret") is None
    assert saved[0]["client_name"] == "Claude Code" and saved[0]["scope"] == "prepza"
    assert counted == [
        ("rate:assistant:mcp:register:testclient", "REGISTRATIONS_PER_IP_HOUR"),
        ("rate:assistant:mcp:register", "REGISTRATIONS_PER_DAY"),
    ]


def test_registering_too_often_is_refused(client, monkeypatch):
    async def over(redis, key, name):
        raise HTTPException(429, "Too many requests. Try again later.")

    monkeypatch.setattr(oauth_limits, "hit_or_skip", over)

    response = client.post("/register", json={"redirect_uris": ["http://localhost/cb"]})

    assert response.status_code == 429


def test_an_app_without_a_secret_revokes_its_token(client, monkeypatch):
    revoked = []
    app_client = OAuthClientInformationFull(
        client_id="c1", redirect_uris=["http://localhost/cb"], token_endpoint_auth_method="none"
    )
    access = Access(
        token="pzm_a", client_id="c1", scopes=["prepza"], grant_id="g", client_name="App"
    )

    async def get_client(self, client_id):
        return app_client if client_id == "c1" else None

    async def load_access_token(self, token):
        return access if token == "pzm_a" else None

    async def revoke_token(self, token):
        revoked.append(token)

    monkeypatch.setattr(oauth_provider.Provider, "get_client", get_client)
    monkeypatch.setattr(oauth_provider.Provider, "load_access_token", load_access_token)
    monkeypatch.setattr(oauth_provider.Provider, "revoke_token", revoke_token)

    response = client.post("/revoke", data={"token": "pzm_a", "client_id": "c1"})

    assert response.status_code == 200 and revoked == [access]
