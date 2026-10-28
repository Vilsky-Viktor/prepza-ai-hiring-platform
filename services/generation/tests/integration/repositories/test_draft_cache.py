import uuid
from types import SimpleNamespace

from redis.asyncio import Redis

from generation.config import settings
from generation.repositories import draft_cache


def test_a_cached_draft_reads_back_and_expires(run, monkeypatch):
    source = f"prompt {uuid.uuid4()}"
    model = SimpleNamespace(model_name="gpt-6.1-sol", reasoning_effort="low")

    async def scenario():
        redis = Redis.from_url(settings.redis_url)
        monkeypatch.setattr(draft_cache, "get_redis", lambda: redis)

        try:
            missing = await draft_cache.get("topics", source, model)
            await draft_cache.put("topics", source, [{"main_topic": "Python"}], model)
            found = await draft_cache.get("topics", source, model)
            ttl = await redis.ttl(draft_cache.cache_key("topics", source, model))
            await redis.delete(draft_cache.cache_key("topics", source, model))
        finally:
            await redis.aclose()

        return missing, found, ttl

    missing, found, ttl = run(scenario())

    assert missing is None
    assert found == [{"main_topic": "Python"}]
    assert ttl > 0
