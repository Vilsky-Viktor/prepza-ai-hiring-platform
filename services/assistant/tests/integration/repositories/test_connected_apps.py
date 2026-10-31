"""How many AI apps a user has connected, for a company's menu: counted by name, without the
connections that have expired, read by companies only."""

import os
import uuid
from datetime import UTC, datetime, timedelta

import httpx
from testee_common.auth.service_auth import issue_token
from testee_common.http.http import bearer

from assistant.helpers.oauth import new_tokens
from assistant.main import app
from assistant.models.oauth import McpGrant
from assistant.repositories import oauth
from tests.integration.transactions import transaction


async def connect(user_id: str, name: str, expires_at: datetime | None = None) -> None:
    """A connection of the user's to an app named `name`, expiring when its refresh token does."""
    client_id = uuid.uuid4().hex
    await transaction(oauth.save_client, client_id, {"client_id": client_id, "client_name": name})
    kept = new_tokens()[1]

    if expires_at is not None:
        kept["refresh_expires_at"] = expires_at

    grant = McpGrant(
        user_id=user_id, client_id=client_id, client_name=name, redirect_host="claude.ai", **kept
    )
    await transaction(oauth.add_grant, grant)


def caller(name: str) -> httpx.AsyncClient:
    token = issue_token(name, "assistant", os.environ["SERVICE_SECRET"])

    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://assistant", headers=bearer(token)
    )


def test_a_users_apps_still_connected_are_counted_once_by_name(run):
    user, other = f"apps-{uuid.uuid4().hex[:8]}", f"apps-{uuid.uuid4().hex[:8]}"
    now = datetime.now(UTC)

    async def scenario():
        # Claude twice, ChatGPT expired, and another user's app.
        await connect(user, "Claude")
        await connect(user, "Claude")
        await connect(user, "ChatGPT", now - timedelta(seconds=1))
        await connect(other, "Cursor")
        counted = await transaction(oauth.connected_app_count, user, now)
        path = f"/internal/users/{user}/active-count"

        async with caller("companies") as client:
            answered = await client.get(path)

        async with caller("library") as client:
            refused = await client.get(path)

        for user_id in (user, other):
            await transaction(oauth.delete_user, user_id)

        return counted, answered, refused

    counted, answered, refused = run(scenario())

    assert counted == 1
    assert answered.json() == {"count": 1}
    assert refused.status_code == 403
