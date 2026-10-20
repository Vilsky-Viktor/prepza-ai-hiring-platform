"""The MCP end-to-end test's client (e2e_tests/mcp.py): HTTP without redirects, an Auth emulator
user, and an app that connects over OAuth with PKCE and calls the MCP endpoint. Standard library
only."""

import base64
import hashlib
import json
import os
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

SITE = os.getenv("E2E_SITE", "http://localhost:8090")
AUTH = os.getenv("E2E_AUTH", "http://localhost:9199")
REDIRECT = "http://127.0.0.1:33418/callback"


def env(name: str) -> str:
    """From the environment, or else from the repo's .env."""
    if os.getenv(name):
        return os.environ[name]

    for line in (Path(__file__).resolve().parents[2] / ".env").read_text().splitlines():
        if line.startswith(f"{name}="):
            return line.split("=", 1)[1].strip()

    sys.exit(f"{name} isn't set")


class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


OPENER = urllib.request.build_opener(NoRedirects)


def send(method: str, url: str, body: bytes | None = None, headers: dict | None = None):
    """(status, headers, parsed JSON or None); errors are answers too."""
    request = urllib.request.Request(url, data=body, method=method, headers=headers or {})

    try:
        with OPENER.open(request, timeout=60) as response:
            raw, status, found = response.read(), response.status, response.headers
    except urllib.error.HTTPError as error:
        raw, status, found = error.read(), error.code, error.headers

    return status, found, json.loads(raw) if raw else None


def post_json(url: str, body, token: str | None = None):
    headers = {"Content-Type": "application/json"}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    return send("POST", url, json.dumps(body).encode(), headers)


def post_form(url: str, fields: dict):
    body = urllib.parse.urlencode(fields).encode()

    return send("POST", url, body, {"Content-Type": "application/x-www-form-urlencoded"})


def check(condition: bool, message: str) -> None:
    if not condition:
        sys.exit(f"FAIL {message}")


def sign_up() -> tuple[str, str, str]:
    """A new emulator user with a verified email: (local id, email, ID token)."""
    email = f"e2e-mcp-{uuid.uuid4().hex[:8]}@example.com"
    status, _, user = post_json(
        f"{AUTH}/identitytoolkit.googleapis.com/v1/accounts:signUp?key=demo",
        {"email": email, "password": "secret123", "returnSecureToken": True},
    )
    check(status == 200, f"sign-up -> {status}")
    # Verified, as a Google sign-in's email is (making a company needs it), then signed in again
    # for a token that says so.
    project = env("FIREBASE_PROJECT_ID")
    send(
        "POST",
        f"{AUTH}/identitytoolkit.googleapis.com/v1/projects/{project}/accounts:update",
        json.dumps({"localId": user["localId"], "emailVerified": True}).encode(),
        {"Authorization": "Bearer owner", "Content-Type": "application/json"},
    )
    status, _, user = post_json(
        f"{AUTH}/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=demo",
        {"email": email, "password": "secret123", "returnSecureToken": True},
    )
    check(status == 200, f"sign-in -> {status}")

    return user["localId"], email, user["idToken"]


def register(client_name: str) -> str:
    """An app registers itself, without a secret: its client id."""
    status, _, client = post_json(
        f"{SITE}/register",
        {
            "client_name": client_name,
            "redirect_uris": [REDIRECT],
            "token_endpoint_auth_method": "none",
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
        },
    )
    check(status == 201 and client.get("client_secret") is None, f"register -> {status}")

    return client["client_id"]


def authorize(client_id: str, challenge: str) -> tuple[str, str]:
    """The app sends the browser to /authorize: (request id, the cookie marking that browser)."""
    query = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "redirect_uri": REDIRECT,
            "response_type": "code",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": "s1",
            "resource": f"{SITE}/mcp",
        }
    )
    status, headers, _ = send("GET", f"{SITE}/authorize?{query}")
    location = headers.get("Location", "")
    check(
        status == 302 and location.startswith(f"{SITE}/connect?request="), f"authorize -> {status}"
    )
    request_id = location.split("request=", 1)[1]
    # The browser that asked is marked; only it may allow the request.
    marked = headers.get("Set-Cookie", "").split(";", 1)[0]
    check(marked == f"prepza_connect={request_id}", f"authorize marks the browser: {marked}")

    return request_id, marked


def allow(id_token: str, client_name: str, request_id: str, marked: str) -> str:
    """The user allows the request on the consent page's API: the code the app gets back."""
    auth = {"Authorization": f"Bearer {id_token}"}
    approve = f"{SITE}/api/assistant/connect/{request_id}/approve"
    status, _, _ = send("POST", approve, headers=auth)
    check(status == 403, f"allowing from another browser -> {status}")
    auth = {**auth, "Cookie": marked}
    status, _, shown = send("GET", f"{SITE}/api/assistant/connect/{request_id}", headers=auth)
    check(status == 200 and shown["redirect_host"] == "127.0.0.1", f"consent -> {status} {shown}")
    check(shown["client_name"] == client_name and shown["known_client"], f"consent shows {shown}")
    status, _, answer = send("POST", approve, headers=auth)
    check(status == 200 and answer["redirect_url"].startswith(REDIRECT), f"approve -> {status}")
    returned = urllib.parse.parse_qs(urllib.parse.urlparse(answer["redirect_url"]).query)
    check(returned["state"] == ["s1"], "the state comes back")
    status, _, _ = send("POST", approve, headers=auth)
    check(status == 404, f"a second answer to the request -> {status}")

    return returned["code"][0]


def exchange(client_id: str, code: str, verifier: str) -> dict:
    """The app exchanges the code for tokens (PKCE); a wrong verifier and a reused code fail."""
    fields = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT,
        "client_id": client_id,
        "code_verifier": verifier,
        "resource": f"{SITE}/mcp",
    }
    status, _, wrong = post_form(f"{SITE}/token", {**fields, "code_verifier": "x" * 50})
    check(status == 400 and wrong["error"] == "invalid_grant", f"a wrong verifier -> {status}")
    status, _, tokens = post_form(f"{SITE}/token", fields)
    check(status == 200 and tokens["access_token"].startswith("pzm_"), f"token -> {status}")
    status, _, _ = post_form(f"{SITE}/token", fields)
    check(status == 400, f"the code a second time -> {status}")

    return tokens


def connect(id_token: str, client_name: str) -> tuple[str, dict]:
    """An app registers, the user allows it and it gets its tokens: (client id, tokens)."""
    client_id = register(client_name)
    verifier = secrets.token_urlsafe(48)
    digest = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
    request_id, marked = authorize(client_id, digest.decode().rstrip("="))
    code = allow(id_token, client_name, request_id, marked)

    return client_id, exchange(client_id, code, verifier)


def rpc(access: str, method: str, params: dict | None = None, number: int = 1):
    """One JSON-RPC call to the MCP endpoint: (status, result or error)."""
    status, _, answer = send(
        "POST",
        f"{SITE}/mcp",
        json.dumps(
            {"jsonrpc": "2.0", "id": number, "method": method, "params": params or {}}
        ).encode(),
        {
            "Authorization": f"Bearer {access}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": "2025-06-18",
        },
    )

    return status, (answer or {}).get("result", answer)


def tool(access: str, name: str, arguments: dict) -> tuple[bool, object]:
    """A tool's (error, data) as the app reads them."""
    status, result = rpc(access, "tools/call", {"name": name, "arguments": arguments})
    check(status == 200, f"tools/call {name} -> {status}")

    return result["isError"], json.loads(result["content"][0]["text"])
