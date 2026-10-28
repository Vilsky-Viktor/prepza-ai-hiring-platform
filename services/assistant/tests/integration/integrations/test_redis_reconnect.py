"""A Redis connection that drops (Redis restarted) doesn't fail the next request."""

from redis.asyncio import Redis

from assistant.config import settings
from assistant.integrations.redis import get_redis


def test_a_dropped_connection_is_replaced_and_the_command_goes_through(run):
    async def scenario():
        redis = get_redis()
        await redis.set("reconnect-check", "1", ex=60)
        connection_id = await redis.client_id()

        async with Redis.from_url(settings.redis_url) as other:
            assert await other.client_kill_filter(_id=connection_id) == 1

        assert await redis.get("reconnect-check") == b"1"
        await redis.delete("reconnect-check")

    run(scenario())
