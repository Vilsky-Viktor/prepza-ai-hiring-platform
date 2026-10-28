"""tools/list and server/discover tell an app how long it may reuse them (2026-07-28)."""

import pytest

from assistant.constants.mcp import CACHE_TTL_MS
from assistant.services import oauth_provider
from tests.unit.services.test_mcp_tools import ACCESS

MODERN = "2026-07-28"
# A connection's token, issued for the MCP endpoint.
BEARER = ACCESS.model_copy(update={"resource": "http://localhost:8090/mcp"})


@pytest.fixture
def bearer(monkeypatch):
    async def load_access_token(self, token):
        return BEARER if token == BEARER.token else None

    monkeypatch.setattr(oauth_provider.Provider, "load_access_token", load_access_token)

    return {"Authorization": f"Bearer {ACCESS.token}"}


def stateless(client, headers: dict, method: str) -> dict:
    meta = {
        "io.modelcontextprotocol/protocolVersion": MODERN,
        "io.modelcontextprotocol/clientCapabilities": {},
    }
    body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": {"_meta": meta}}
    sent = {
        **headers,
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": MODERN,
        "Mcp-Method": method,
    }
    response = client.post("/mcp", json=body, headers=sent)

    assert response.status_code == 200, response.text

    return response.json()["result"]


def test_the_tools_may_be_reused_only_by_the_same_caller(client, bearer):
    listed = stateless(client, bearer, "tools/list")

    assert (listed["ttlMs"], listed["cacheScope"]) == (CACHE_TTL_MS, "private")


def test_the_servers_description_may_be_reused_by_anyone(client, bearer):
    discovered = stateless(client, bearer, "server/discover")

    assert (discovered["ttlMs"], discovered["cacheScope"]) == (CACHE_TTL_MS, "public")


def test_the_tools_keep_their_order(client, bearer):
    first = [tool["name"] for tool in stateless(client, bearer, "tools/list")["tools"]]
    second = [tool["name"] for tool in stateless(client, bearer, "tools/list")["tools"]]

    assert first == second and len(first) > 1
