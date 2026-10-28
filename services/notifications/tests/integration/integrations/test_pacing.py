from collections import Counter
from uuid import uuid4

from prepza_common.http import pacing
from prepza_common.http.pacing import wait_turn

from notifications.constants.email import RESEND_PACE_KEY, RESEND_PER_SECOND
from notifications.integrations.redis import get_redis


def test_no_second_takes_more_than_resends_share(run, monkeypatch):
    # Its own key, so no other test's sends count against it.
    key = f"{RESEND_PACE_KEY}:{uuid4()}"
    counted = pacing.counted
    # The second each send was let through in, as Redis counted it (never the clock read after
    # it returns, which a slow machine can read in the next second).
    taken = Counter()

    async def counting(redis, second_key, *args):
        total, ttl = await counted(redis, second_key, *args)

        if total <= RESEND_PER_SECOND:
            taken[second_key] += 1

        return total, ttl

    monkeypatch.setattr(pacing, "counted", counting)

    async def scenario():
        for _ in range(RESEND_PER_SECOND * 2 + 1):
            await wait_turn(get_redis(), key, RESEND_PER_SECOND)

    run(scenario())

    assert sum(taken.values()) == RESEND_PER_SECOND * 2 + 1
    assert max(taken.values()) <= RESEND_PER_SECOND
