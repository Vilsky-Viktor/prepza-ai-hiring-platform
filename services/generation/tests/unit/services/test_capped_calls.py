"""A job's fan-out of model calls runs GENERATION_CALLS_AT_ONCE at a time (as set in the Controls
tab), not all at once: the key self-checks."""

import asyncio

from generation.services import key_self_check


def counting():
    """A call that notes how many run at once; and the most seen."""
    state = {"running": 0, "most": 0}

    async def call(*args):
        state["running"] += 1
        state["most"] = max(state["most"], state["running"])
        await asyncio.sleep(0)
        state["running"] -= 1

    return call, state


def test_key_self_checks_run_capped(redis, monkeypatch):
    redis.limits["GENERATION_CALLS_AT_ONCE"] = "3"
    check, state = counting()
    monkeypatch.setattr(key_self_check, "self_check", check)
    questions = [{"text": f"Question {index}", "options": []} for index in range(7)]

    kept = asyncio.run(key_self_check.keys_that_hold(questions, "Bookkeeping", "basic"))

    assert state["most"] == 3
    assert kept == questions
