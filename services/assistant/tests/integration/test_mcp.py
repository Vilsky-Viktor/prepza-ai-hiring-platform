"""An AI app connecting over MCP, end to end in-process: the MCP SDK's own OAuth client registers,
the user allows it with their emulator ID token, the code is exchanged with PKCE and the tools
are called as the user against the running stack's services. Reads only, and a write the checks
refuse, so nothing is left behind; the user is deleted after the test."""

import json
import uuid

import firebase_admin
import httpx2
from mcp import Client
from mcp.client.auth.oauth2 import OAuthClientProvider
from mcp.client.streamable_http import streamable_http_client
from mcp.shared.auth import AuthorizationCodeResult, OAuthClientMetadata

from app.config.settings import settings
from app.constants.chat import OTHER_COMPANY
from app.main import app
from app.routers import mcp as mcp_router
from app.storage import oauth

REDIRECT = "http://127.0.0.1:33418/callback"


class Memory:
    """Where the app keeps its tokens and registration (the SDK's TokenStorage)."""

    def __init__(self):
        self.tokens = self.client = None

    async def get_tokens(self):
        return self.tokens

    async def set_tokens(self, tokens):
        self.tokens = tokens

    async def get_client_info(self):
        return self.client

    async def set_client_info(self, client_info):
        self.client = client_info


def site_client(auth=None) -> httpx2.AsyncClient:
    transport = httpx2.ASGITransport(app=app)

    return httpx2.AsyncClient(transport=transport, base_url=settings.site_url, auth=auth)


async def connected(id_token: str, storage: Memory):
    """The SDK's OAuth client, which allows itself on the consent page's API as the user."""
    answered = {}

    async def redirect_handler(url: str) -> None:
        async with site_client() as site:
            authorized = await site.get(url)
            request_id = authorized.headers["location"].split("request=", 1)[1]
            # The cookie that marks this browser as the one that asked (its path is the
            # gateway's /api/assistant/connect, so it's passed by hand here).
            marked = authorized.headers["set-cookie"].split(";", 1)[0]
            headers = {"Authorization": f"Bearer {id_token}", "Cookie": marked}
            shown = (await site.get(f"/connect/{request_id}", headers=headers)).json()
            approved = await site.post(f"/connect/{request_id}/approve", headers=headers)

        answered["shown"] = shown
        answered["url"] = httpx2.URL(approved.json()["redirect_url"])

    async def callback_handler() -> AuthorizationCodeResult:
        params = answered["url"].params

        # The answer names its issuer (RFC 9207), which the SDK checks against the metadata's.
        return AuthorizationCodeResult(
            code=params["code"], state=params.get("state"), iss=params.get("iss")
        )

    metadata = OAuthClientMetadata(
        client_name="Integration app",
        redirect_uris=[REDIRECT],
        token_endpoint_auth_method="none",
        grant_types=["authorization_code", "refresh_token"],
        response_types=["code"],
    )
    provider = OAuthClientProvider(
        f"{settings.site_url}/mcp", metadata, storage, redirect_handler, callback_handler
    )

    return provider, answered


def test_an_app_connects_with_oauth_and_calls_tools_as_the_user(run, user):
    uid, id_token = user
    storage = Memory()

    if not firebase_admin._apps:
        firebase_admin.initialize_app(options={"projectId": settings.firebase_project_id})

    async def scenario():
        provider, answered = await connected(id_token, storage)

        async with mcp_router.running(), site_client(provider) as http:
            transport = streamable_http_client(f"{settings.site_url}/mcp", http_client=http)

            async with Client(transport) as client:
                listed = await client.list_tools()
                me = await client.call_tool("get_me", {})
                companies = await client.call_tool("list_companies", {})
                refused = await client.call_tool(
                    "rename_company", {"company_id": str(uuid.uuid4()), "title": "Nope"}
                )
                excluded = await client.call_tool("delete_account", {})

        return answered, listed, me, companies, refused, excluded, await oauth.of_user(uid)

    answered, listed, me, companies, refused, excluded, grants = run(scenario())

    assert answered["shown"] == {
        "client_name": "Integration app",
        "redirect_host": "127.0.0.1",
        "known_client": True,
        "read_only": False,
    }
    names = {tool.name for tool in listed.tools}
    assert "get_me" in names and not names & {"delete_account", "delete_company"}
    assert not me.is_error
    assert json.loads(me.content[0].text)["data"]["email"].startswith("assistant-")
    assert json.loads(companies.content[0].text)["data"] == []
    # Someone else's company: refused before anything is sent.
    assert refused.is_error and OTHER_COMPANY in refused.content[0].text
    assert excluded.is_error
    assert [(grant.client_name, grant.redirect_host) for grant in grants] == [
        ("Integration app", "127.0.0.1")
    ]
    assert storage.tokens.access_token.startswith("pzm_")
