"""The funnel's mcp_active event, against the real database and Redis: once a day for each user
and app, however often the app calls."""

import uuid

from prepza_common.config.constants import DAY_SECONDS

from app.constants.mcp import ACTIVE_KEY
from app.integrations.redis import get_redis
from app.models.oauth_tokens import Access
from app.services import mcp_tools
from app.storage import oauth
from tests.integration.test_oauth_storage import connect


def access(user: str, grant_id: uuid.UUID, client_name: str) -> Access:
    return Access(
        token="pzm_x",
        client_id="c1",
        scopes=["prepza"],
        subject=user,
        grant_id=str(grant_id),
        client_name=client_name,
    )


def test_an_app_in_use_is_counted_active_once_a_day(run, monkeypatch):
    user = f"active-{uuid.uuid4().hex[:8]}"
    tracked = []

    async def track(event, **props):
        tracked.append((event, props))

    monkeypatch.setattr(mcp_tools, "track", track)

    async def scenario():
        claude, _ = await connect(user)
        chatgpt, _ = await connect(user)
        await mcp_tools.mark_active(access(user, claude.id, "Claude"))
        await mcp_tools.mark_active(access(user, claude.id, "Claude"))
        await mcp_tools.mark_active(access(user, chatgpt.id, "ChatGPT"))
        keys = [ACTIVE_KEY.format(user_id=user, client=name) for name in ("claude", "chatgpt")]
        expiry = [await get_redis().ttl(key) for key in keys]
        await get_redis().delete(*keys)

        return expiry, {grant.id: grant.last_used_at for grant in await oauth.of_user(user)}

    expiry, last_used = run(scenario())

    assert tracked == [
        ("mcp_active", {"user_id": user, "client": "claude"}),
        ("mcp_active", {"user_id": user, "client": "chatgpt"}),
    ]
    # Counted again once the day is over.
    assert all(DAY_SECONDS - 60 < seconds <= DAY_SECONDS for seconds in expiry)
    assert all(when is not None for when in last_used.values())
