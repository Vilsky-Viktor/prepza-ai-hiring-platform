"""End-to-end test of the MCP server (AI apps such as Claude and ChatGPT) against the running local
stack, through the gateway, as an app would: it registers itself, the user allows it on the
consent page's API, it exchanges the code (PKCE) for tokens and calls tools; then refreshes,
revokes, and a second connection is disconnected by the user. A throwaway Auth emulator user;
its account is deleted at the end (which also deletes its connections and company).

Usage: python3 e2e_tests/mcp.py   (standard library only; the client is helpers/mcp_client.py)
"""

import json
import uuid

from helpers.mcp_client import (
    AUTH,
    SITE,
    check,
    connect,
    env,
    post_form,
    post_json,
    rpc,
    send,
    sign_up,
    stateless_rpc,
    tool,
)

EXCLUDED = {"delete_account", "delete_company"}


def step(message: str) -> None:
    print(f"- {message}", flush=True)


def discovery() -> None:
    step("the endpoint without a token is a 401 that names its resource metadata")
    status, headers, _ = send("POST", f"{SITE}/mcp", b"{}", {"Content-Type": "application/json"})
    check(status == 401 and "resource_metadata=" in headers.get("WWW-Authenticate", ""), "401")
    status, _, metadata = send("GET", f"{SITE}/.well-known/oauth-protected-resource/mcp")
    check(status == 200 and metadata["authorization_servers"] == [SITE], f"resource {metadata}")
    # Some apps look for it at the root, without the resource's path: the same document.
    status, _, root = send("GET", f"{SITE}/.well-known/oauth-protected-resource")
    check(status == 200 and root == metadata, f"root resource metadata {root}")
    status, _, server = send("GET", f"{SITE}/.well-known/oauth-authorization-server")
    check(status == 200 and server["issuer"] == SITE, f"authorization server {server}")


def tool_list(access: str) -> None:
    step("initialize, tools/list (the account's and a company's deletion aren't there)")
    status, started = rpc(
        access,
        "initialize",
        {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "e2e", "version": "1"},
        },
    )
    check(status == 200 and started["serverInfo"]["name"] == "testee", f"initialize {started}")
    status, listed = rpc(access, "tools/list")
    names = {item["name"] for item in listed["tools"]}
    check(status == 200 and "get_me" in names and not names & EXCLUDED, f"{len(names)} tools")
    create = next(item for item in listed["tools"] if item["name"] == "create_company")
    check(create["annotations"]["readOnlyHint"] is False, "create_company is a write")
    print(f"  {len(names)} tools")

    step("the newest revision (2026-07-28): stateless calls without initialize")
    status, listed = stateless_rpc(access, "tools/list")
    check(status == 200 and {item["name"] for item in listed["tools"]} == names, "tools/list")
    arguments = {"name": "get_me", "arguments": {}}
    status, called = stateless_rpc(access, "tools/call", arguments, "get_me")
    check(status == 200 and called["isError"] is False, f"tools/call {called}")


def tools_as_the_user(access: str, email: str) -> str:
    """get_me, create_company and list_companies as the user: the new company's id."""
    step("tools as the user: get_me, then create_company and list_companies")
    error, me = tool(access, "get_me", {})
    check(not error and me["data"]["email"] == email, f"get_me {me}")
    name = f"MCP e2e {uuid.uuid4().hex[:6]}"
    error, made = tool(access, "create_company", {"name": name})
    check(not error and made["data"]["name"] == name, f"create_company {made}")
    check(all(link.startswith(SITE) for link in made.get("links", [])), "links are absolute")
    error, companies = tool(access, "list_companies", {})
    check(any(item["name"] == name for item in companies["data"]), "the new company is listed")
    error, _ = tool(access, "delete_company", {"company_id": made["data"]["id"]})
    check(error, "delete_company is refused")

    return made["data"]["id"]


def api_keys(id_token: str, company_id: str) -> None:
    step("an API key: only with the mcp permission, only its company, only its tools")
    keys = f"{SITE}/api/v1/manage/keys?company_id={company_id}"
    _, _, plain = post_json(keys, {"name": "No MCP", "expiry": "1"}, id_token)
    check(rpc(plain["key"], "tools/list")[0] == 401, "a key without mcp is refused")
    permissions = ["mcp", "candidates:read"]
    status, _, agent = post_json(
        keys, {"name": "Agent", "expiry": "1", "permissions": permissions}, id_token
    )
    check(status == 201, f"key -> {status}")
    status, listed = rpc(agent["key"], "tools/list")
    names = {item["name"] for item in listed["tools"]}
    check(status == 200 and "list_candidates" in names, f"{len(names)} key tools")
    check(not names & {"get_me", "invite_candidate", "list_members"}, "only its tools")
    error, own = tool(agent["key"], "get_company", {"company_id": company_id})
    check(not error and own["data"]["id"] == company_id, f"its company {own}")
    error, _ = tool(
        agent["key"], "invite_candidate", {"interview_id": company_id, "email": "a@b.co"}
    )
    check(error, "a tool beyond its permissions is refused")
    allowed_ips(id_token, company_id, agent["id"], agent["key"])


# Locally the caller's address is the gateway's, on Docker's private network; elsewhere a private
# address too. 203.0.113.0/24 is a documentation range no caller has.
PRIVATE = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "127.0.0.0/8", "fc00::/7", "::1"]


def allowed_ips(id_token: str, company_id: str, key_id: str, key: str) -> None:
    step("an API key limited to allowed IPs: refused elsewhere, working from its address")
    path = f"{SITE}/api/v1/manage/keys/{key_id}/allowed-ips?company_id={company_id}"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {id_token}"}

    def limit(addresses: list[str]) -> None:
        body = json.dumps({"allowed_ips": addresses}).encode()
        status, _, saved = send("PUT", path, body, headers)
        check(status == 200 and saved["allowed_ips"] == addresses, f"allowed IPs -> {status}")

    limit(["203.0.113.0/24"])
    status, refused = rpc(key, "tools/list")
    check(status == 403 and refused["code"] == "ip_not_allowed", f"elsewhere -> {status}")
    limit(PRIVATE)
    status, listed = rpc(key, "tools/list")
    check(status == 200 and listed["tools"], f"from its address -> {status}")


def listed_connections(id_token: str) -> list[dict]:
    auth = {"Authorization": f"Bearer {id_token}"}
    status, _, connections = send("GET", f"{SITE}/api/assistant/connections", headers=auth)
    check(status == 200, f"connections -> {status}")

    return connections


def refresh_and_revoke(client_id: str, tokens: dict) -> None:
    step("refresh: new tokens; the old refresh token and access stop working")
    access = tokens["access_token"]
    refresh = {
        "grant_type": "refresh_token",
        "refresh_token": tokens["refresh_token"],
        "client_id": client_id,
    }
    # A refresh for another resource is refused (RFC 8707), and leaves the token working.
    other = {**refresh, "resource": "https://other.example/mcp"}
    status, _, refused = post_form(f"{SITE}/token", other)
    check(status == 400 and refused["error"] == "invalid_target", f"another resource {refused}")
    status, _, renewed = post_form(f"{SITE}/token", refresh)
    check(status == 200 and renewed["access_token"] != access, f"refresh -> {status}")
    status, _, _ = post_form(f"{SITE}/token", refresh)
    check(status == 400, f"the old refresh token -> {status}")
    check(rpc(access, "tools/list")[0] == 401, "the old access token is refused")
    access = renewed["access_token"]
    check(rpc(access, "tools/list")[0] == 200, "the new access token works")

    step("the app revokes its token: the connection is gone")
    status, _, _ = post_form(f"{SITE}/revoke", {"token": access, "client_id": client_id})
    check(status == 200 and rpc(access, "tools/list")[0] == 401, "revoked")


def disconnect(id_token: str) -> None:
    step("a second app; the user disconnects it")
    _, second = connect(id_token, "Second app")
    connections = listed_connections(id_token)
    check([item["client_name"] for item in connections] == ["Second app"], "one connection")
    url = f"{SITE}/api/assistant/connections/{connections[0]['id']}"
    status, _, _ = send("DELETE", url, headers={"Authorization": f"Bearer {id_token}"})
    check(status == 204 and rpc(second["access_token"], "tools/list")[0] == 401, "disconnected")


def delete_account(project: str, local_id: str, id_token: str) -> None:
    """The account goes the way a user deletes it (with its company and connections)."""
    send("DELETE", f"{SITE}/api/accounts/me", headers={"Authorization": f"Bearer {id_token}"})
    send(
        "POST",
        f"{AUTH}/identitytoolkit.googleapis.com/v1/projects/{project}/accounts:delete",
        json.dumps({"localId": local_id}).encode(),
        {"Authorization": "Bearer owner", "Content-Type": "application/json"},
    )
    print("clean-up: the throwaway account is deleted")


def main() -> None:
    project = env("FIREBASE_PROJECT_ID")
    local_id, email, id_token = sign_up()

    try:
        discovery()
        step("an app registers, the user allows it, and it gets tokens with PKCE")
        client_id, tokens = connect(id_token, "E2E app")
        tool_list(tokens["access_token"])
        company_id = tools_as_the_user(tokens["access_token"], email)
        api_keys(id_token, company_id)
        step("the connection is listed for the user")
        names = [item["client_name"] for item in listed_connections(id_token)]
        check(names == ["E2E app"], "listed")
        refresh_and_revoke(client_id, tokens)
        disconnect(id_token)
    finally:
        delete_account(project, local_id, id_token)

    print("mcp ok")


if __name__ == "__main__":
    main()
