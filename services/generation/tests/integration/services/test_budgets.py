import uuid

from redis.asyncio import Redis

from generation.config import settings
from generation.constants.generation import BUDGET_KEY_SECONDS
from generation.services import budget


def test_todays_uses_are_counted_in_redis_and_read_back_as_the_budgets_use(run, monkeypatch):
    key = f"test:budget:{uuid.uuid4()}"

    async def scenario():
        redis = Redis.from_url(settings.redis_url)
        monkeypatch.setattr(budget, "get_redis", lambda: redis)
        monkeypatch.setattr(budget, "BUDGETS", {"DAILY_GENERATION_LIMIT": key})

        try:
            counts = [await budget.count_today(key), await budget.count_today(key)]
            ttl = await redis.ttl(budget.day_key(key))
            [found] = await budget.budgets()
        finally:
            await redis.delete(budget.day_key(key))
            await redis.aclose()

        return counts, ttl, found

    counts, ttl, found = run(scenario())

    assert counts == [1, 2]
    assert 0 < ttl <= BUDGET_KEY_SECONDS
    assert (found.name, found.used) == ("DAILY_GENERATION_LIMIT", 2)
