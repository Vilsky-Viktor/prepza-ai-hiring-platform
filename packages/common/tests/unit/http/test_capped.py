import asyncio

from testee_common.http.capped import gather_capped


def test_no_more_than_the_cap_run_at_once_and_results_keep_their_order():
    running, most = [0], [0]

    async def call(value):
        running[0] += 1
        most[0] = max(most[0], running[0])
        # Lets the others start, if the cap allowed them to.
        await asyncio.sleep(0)
        running[0] -= 1

        return value

    results = asyncio.run(gather_capped(2, (call(value) for value in range(6))))

    assert results == list(range(6))
    assert most[0] == 2


def test_failures_come_back_in_place_when_asked():
    async def call(value):
        if value == 1:
            raise ValueError(value)

        return value

    results = asyncio.run(gather_capped(1, [call(0), call(1), call(2)], return_exceptions=True))

    assert results[0] == 0 and isinstance(results[1], ValueError) and results[2] == 2


def test_a_cap_below_one_still_runs_the_calls():
    async def call():
        return "done"

    assert asyncio.run(gather_capped(0, [call()])) == ["done"]
