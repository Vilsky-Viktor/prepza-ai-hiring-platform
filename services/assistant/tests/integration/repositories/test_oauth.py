"""AI apps' registrations and connections against the real database and Redis: tokens kept as
hashes, refresh racing, disconnecting, deleting an account, and the daily clean-up."""

import os
import uuid
from datetime import UTC, datetime, timedelta

import httpx
from prepza_common.auth.service_auth import issue_token
from prepza_common.auth.tokens import hashed
from prepza_common.http.http import bearer
from sqlalchemy import update

from assistant.core.db import Session
from assistant.helpers.oauth import new_tokens
from assistant.main import app
from assistant.models.oauth import McpGrant, OAuthClient
from assistant.repositories import oauth, oauth_requests


def internal() -> httpx.AsyncClient:
    """The assistant's internal routes, called as library (deleting or exporting an account)."""
    token = issue_token("library", "assistant", os.environ["SERVICE_SECRET"])

    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://assistant",
        headers=bearer(token),
    )


async def connect(user_id: str, client_id: str | None = None) -> tuple[McpGrant, dict]:
    """A registered app and a connection of the user's to it: (the row, its tokens)."""
    client_id = client_id or uuid.uuid4().hex
    await oauth.save_client(client_id, {"client_id": client_id, "client_name": "App"})
    token, kept = new_tokens()
    grant = McpGrant(
        user_id=user_id, client_id=client_id, client_name="App", redirect_host="claude.ai", **kept
    )

    return await oauth.add_grant(grant), token.model_dump()


def test_a_connection_is_found_by_its_tokens_hashes_only(run):
    user = f"oauth-{uuid.uuid4().hex[:8]}"

    async def scenario():
        grant, tokens = await connect(user)
        by_access = await oauth.by_access(hashed(tokens["access_token"]))
        by_refresh = await oauth.by_refresh(hashed(tokens["refresh_token"]))
        by_raw = await oauth.by_access(tokens["access_token"])

        return grant, by_access, by_refresh, by_raw

    grant, by_access, by_refresh, by_raw = run(scenario())

    assert by_access.id == by_refresh.id == grant.id
    assert by_raw is None


def test_of_two_refreshes_with_one_token_only_the_first_gets_new_tokens(run):
    user = f"oauth-{uuid.uuid4().hex[:8]}"

    async def scenario():
        grant, tokens = await connect(user)
        old = hashed(tokens["refresh_token"])
        first = await oauth.rotate(grant.id, old, new_tokens()[1])
        second = await oauth.rotate(grant.id, old, new_tokens()[1])

        replaced = await oauth.by_previous_refresh(old)

        return first, second, await oauth.by_refresh(old), replaced, grant.id

    first, second, current, replaced, grant_id = run(scenario())

    assert (first, second, current) == (True, False, None)
    # The replaced token is remembered, with when, to tell a late reuse from a race.
    assert replaced.id == grant_id and replaced.refreshed_at is not None


def test_last_used_is_written_at_most_once_an_hour(run):
    user = f"oauth-{uuid.uuid4().hex[:8]}"
    now = datetime.now(UTC)

    async def scenario():
        grant, _ = await connect(user)
        await oauth.used(grant.id, now)
        await oauth.used(grant.id, now + timedelta(minutes=30))
        first = (await oauth.of_user(user))[0].last_used_at
        await oauth.used(grant.id, now + timedelta(minutes=61))

        return first, (await oauth.of_user(user))[0].last_used_at

    first, later = run(scenario())

    assert first == now
    assert later == now + timedelta(minutes=61)


def test_a_user_disconnects_only_their_own_and_deleting_the_account_removes_the_rest(run):
    ann, bob = f"ann-{uuid.uuid4().hex[:8]}", f"bob-{uuid.uuid4().hex[:8]}"

    async def scenario():
        first, _ = await connect(ann)
        await connect(ann)
        bobs, _ = await connect(bob)
        not_hers = await oauth.remove(bobs.id, ann)
        removed = await oauth.remove(first.id, ann)
        left = len(await oauth.of_user(ann))

        async with internal() as api:
            await api.request("DELETE", f"/internal/users/{ann}", json={"email": "a@example.com"})

        return not_hers, removed, left, await oauth.of_user(ann), await oauth.of_user(bob)

    not_hers, removed, left, ann_after, bob_after = run(scenario())

    assert not_hers is None and removed.user_id == ann
    assert left == 1
    assert ann_after == [] and len(bob_after) == 1


def test_the_export_lists_the_connected_apps(run):
    user = f"oauth-{uuid.uuid4().hex[:8]}"

    async def scenario():
        await connect(user)

        async with internal() as api:
            response = await api.post(
                f"/internal/users/{user}/export", json={"email": "a@example.com"}
            )

        return response.json()

    [connected] = run(scenario())["connected_ai_apps"]

    assert (connected["client_name"], connected["redirect_host"]) == ("App", "claude.ai")
    assert "access_hash" not in connected


def test_retention_deletes_expired_connections_and_idle_apps(run):
    user = f"oauth-{uuid.uuid4().hex[:8]}"

    async def scenario():
        expired, _ = await connect(user)
        kept, _ = await connect(user)
        idle = uuid.uuid4().hex
        await oauth.save_client(idle, {"client_id": idle})

        async with Session() as session:
            past = datetime.now(UTC) - timedelta(days=31)
            await session.execute(
                update(McpGrant).where(McpGrant.id == expired.id).values(refresh_expires_at=past)
            )
            await session.execute(
                update(OAuthClient)
                .where(OAuthClient.client_id.in_([idle, expired.client_id]))
                .values(created_at=past)
            )
            await session.commit()

        async with internal() as api:
            await api.post("/internal/schedules/retention")

        left = [grant.id for grant in await oauth.of_user(user)]

        return left, kept.id, await oauth.get_client(idle), await oauth.get_client(kept.client_id)

    left, kept_id, idle_client, kept_client = run(scenario())

    assert left == [kept_id]
    assert idle_client is None and kept_client is not None


def test_a_request_and_a_code_are_taken_once(run):
    async def scenario():
        await oauth_requests.save_request("r1", {"client_id": "c"})
        await oauth_requests.save_code("h1", {"client_id": "c"})

        return (
            await oauth_requests.peek_request("r1"),
            await oauth_requests.take_request("r1"),
            await oauth_requests.take_request("r1"),
            await oauth_requests.take_code("h1"),
            await oauth_requests.take_code("h1"),
        )

    peeked, taken, again, code, code_again = run(scenario())

    assert peeked == taken == code == {"client_id": "c"}
    assert again is None and code_again is None


def test_a_metadata_document_app_keeps_its_long_id_and_newest_copy_and_connections(run):
    """An app named by its metadata document's address (longer than a registration's id): a new
    read replaces its copy and when it was read, and its connections stay."""
    client_id = f"https://app-{uuid.uuid4().hex}.example.com/oauth/clients/prepza/metadata.json"
    first = datetime(2026, 10, 1, tzinfo=UTC)

    async def scenario():
        await oauth.keep_document(client_id, {"client_id": client_id, "client_name": "A"}, first)
        grant, _ = await connect("doc-user-" + uuid.uuid4().hex[:8], client_id)
        later = first + timedelta(days=2)
        await oauth.keep_document(client_id, {"client_id": client_id, "client_name": "B"}, later)
        found = await oauth.read_document(client_id)
        still = await oauth.by_access(grant.access_hash)

        return found, still, grant

    (info, read_at), still, grant = run(scenario())

    assert len(client_id) > 64
    assert info["client_name"] == "B" and read_at == first + timedelta(days=2)
    assert still.id == grant.id
