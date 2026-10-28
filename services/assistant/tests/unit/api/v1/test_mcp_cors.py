import httpx
import pytest
from prepza_common.http import http

SITE = "http://localhost:8090"
INSPECTOR = "http://localhost:6274"
# Every endpoint a browser-based app calls: the MCP endpoint and the OAuth server's.
ENDPOINTS = [
    ("/mcp", "POST"),
    ("/token", "POST"),
    ("/register", "POST"),
    ("/revoke", "POST"),
    ("/.well-known/oauth-authorization-server", "GET"),
    ("/.well-known/oauth-protected-resource/mcp", "GET"),
    ("/.well-known/oauth-protected-resource", "GET"),
]


def preflight(client, path, method, origin):
    return client.options(
        path,
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": "content-type",
        },
    )


@pytest.mark.parametrize(("path", "method"), ENDPOINTS)
def test_only_the_site_and_known_browser_apps_may_call_from_a_page(client, path, method):
    for origin in (SITE, INSPECTOR):
        allowed = preflight(client, path, method, origin)

        assert allowed.status_code == 200
        assert allowed.headers["access-control-allow-origin"] == origin
        assert "access-control-allow-credentials" not in allowed.headers

    refused = preflight(client, path, method, "https://evil.example")

    assert refused.status_code == 400
    assert "access-control-allow-origin" not in refused.headers


def test_a_page_elsewhere_gets_no_cors_answer_and_a_server_needs_none(client):
    from_page = client.get(
        "/.well-known/oauth-authorization-server", headers={"Origin": "https://evil.example"}
    )
    from_server = client.get("/.well-known/oauth-authorization-server")

    assert from_page.status_code == 200 == from_server.status_code
    assert "access-control-allow-origin" not in from_page.headers
    assert from_server.json()["issuer"] == SITE


def test_an_api_keys_agent_is_checked_from_the_address_it_called_from(client, monkeypatch):
    sent = []

    class Client:
        async def post(self, url, json, headers):
            sent.append(json)

            return httpx.Response(
                403,
                json={
                    "detail": "This API key can't be used from this IP address.",
                    "code": "ip_not_allowed",
                },
                request=httpx.Request("POST", url),
            )

    monkeypatch.setattr(http, "get_client", Client)
    # As Google's load balancer forwards it: the client, then itself.
    headers = {"Authorization": "Bearer pz_key", "X-Forwarded-For": "203.0.113.7, 34.1.2.3"}

    response = client.post("/mcp", json={}, headers=headers)

    assert sent == [{"key": "pz_key", "ip": "203.0.113.7"}]
    assert response.status_code == 403
    assert response.json()["code"] == "ip_not_allowed"
