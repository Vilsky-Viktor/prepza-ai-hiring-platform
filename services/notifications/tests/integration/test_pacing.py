import time

from app.constants.email import RESEND_PER_SECOND
from app.services import pacing


def test_no_second_takes_more_than_resends_share(run):
    async def scenario():
        seconds = []

        for _ in range(RESEND_PER_SECOND * 2 + 1):
            await pacing.wait_turn()
            seconds.append(int(time.time()))

        return seconds

    seconds = run(scenario())

    assert max(seconds.count(second) for second in set(seconds)) <= RESEND_PER_SECOND
