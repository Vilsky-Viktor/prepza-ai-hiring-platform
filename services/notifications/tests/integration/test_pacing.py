import time
from uuid import uuid4

from prepza_common.pacing import wait_turn

from app.constants.email import RESEND_PACE_KEY, RESEND_PER_SECOND
from app.integrations.redis import get_redis


def test_no_second_takes_more_than_resends_share(run):
    # Its own key, so no other test's sends count against it.
    key = f"{RESEND_PACE_KEY}:{uuid4()}"

    async def scenario():
        seconds = []

        for _ in range(RESEND_PER_SECOND * 2 + 1):
            await wait_turn(get_redis(), key, RESEND_PER_SECOND)
            seconds.append(int(time.time()))

        return seconds

    seconds = run(scenario())

    assert max(seconds.count(second) for second in set(seconds)) <= RESEND_PER_SECOND
