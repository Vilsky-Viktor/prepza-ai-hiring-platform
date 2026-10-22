"""Calls run together, at most so many at a time: a job's fan-out of model or service calls stays
within its share of what's shared (OpenAI's rate, another service's slots)."""

import asyncio
from collections.abc import Awaitable, Iterable


async def gather_capped(at_once: int, calls: Iterable[Awaitable], return_exceptions=False) -> list:
    """asyncio.gather of `calls`, of which at most `at_once` run at a time; results in order."""
    gate = asyncio.Semaphore(max(int(at_once), 1))

    async def one(call: Awaitable):
        async with gate:
            return await call

    return list(
        await asyncio.gather(*(one(call) for call in calls), return_exceptions=return_exceptions)
    )
