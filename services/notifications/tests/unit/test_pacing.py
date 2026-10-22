import asyncio

from app.services import pacing


def test_a_request_over_the_seconds_share_waits_for_the_next_second(monkeypatch):
    totals = iter([9, 1])
    slept = []

    async def counted(redis, key, amount, window):
        return next(totals), window

    async def sleep(seconds):
        slept.append(seconds)

    monkeypatch.setattr(pacing, "counted", counted)
    monkeypatch.setattr(pacing.asyncio, "sleep", sleep)
    asyncio.run(pacing.wait_turn())

    assert len(slept) == 1 and 0 <= slept[0] <= 1


def test_with_redis_down_sending_goes_on_unpaced(monkeypatch):
    async def counted(redis, key, amount, window):
        raise ConnectionError("down")

    monkeypatch.setattr(pacing, "counted", counted)

    asyncio.run(pacing.wait_turn())
