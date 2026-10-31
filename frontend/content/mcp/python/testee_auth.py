# Signs your agent in to testee's MCP server, shared by the examples.
# pip install "mcp==1.30.0"
import asyncio
import json
import os
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from mcp.client.auth import OAuthClientProvider, TokenStorage
from mcp.shared.auth import OAuthClientInformationFull, OAuthClientMetadata, OAuthToken

TESTEE_MCP = os.environ.get("TESTEE_MCP", "https://testee.ai/mcp")
REDIRECT = "http://localhost:8765/callback"
STORE = Path("testee-tokens.json")


class FileStorage(TokenStorage):
    """The tokens in a file: each refresh replaces both, so the new ones must be kept."""

    def read(self, key: str):
        return json.loads(STORE.read_text()).get(key) if STORE.exists() else None

    def write(self, key: str, value) -> None:
        kept = json.loads(STORE.read_text()) if STORE.exists() else {}
        STORE.write_text(json.dumps({**kept, key: value.model_dump(mode="json")}))

    async def get_tokens(self) -> OAuthToken | None:
        found = self.read("tokens")

        return OAuthToken.model_validate(found) if found else None

    async def set_tokens(self, tokens: OAuthToken) -> None:
        self.write("tokens", tokens)

    async def get_client_info(self) -> OAuthClientInformationFull | None:
        found = self.read("client")

        return OAuthClientInformationFull.model_validate(found) if found else None

    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        self.write("client", client_info)


def wait_for_code() -> tuple[str, str | None]:
    """The code testee's consent page sends back to this computer once you allow the agent."""
    found = {}

    class Callback(BaseHTTPRequestHandler):
        def do_GET(self):
            found.update(parse_qs(urlparse(self.path).query))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Signed in to testee. You can close this tab.")

    HTTPServer(("localhost", 8765), Callback).handle_request()

    return found["code"][0], found.get("state", [None])[0]


async def open_browser(url: str) -> None:
    webbrowser.open(url)


async def callback() -> tuple[str, str | None]:
    return await asyncio.to_thread(wait_for_code)


def connection() -> dict:
    """With TESTEE_API_KEY set, the agent signs in with that company API key (a server, no
    browser); otherwise as you, allowing it once in the browser."""
    key = os.environ.get("TESTEE_API_KEY")

    if key:
        return {"headers": {"Authorization": f"Bearer {key}"}}

    metadata = OAuthClientMetadata(client_name="My agent", redirect_uris=[REDIRECT])
    provider = OAuthClientProvider(
        server_url=TESTEE_MCP,
        client_metadata=metadata,
        storage=FileStorage(),
        redirect_handler=open_browser,
        callback_handler=callback,
    )

    return {"auth": provider}
