"""Retries without a client's key, against real Redis: a derived key returns the first result
within its window, a client's key used for another request is refused, and a failure frees the
key."""

import asyncio
import uuid

import pytest
from fastapi import HTTPException

from api.integrations.redis import get_redis
from api.services.idempotency import fingerprint, once, slot


def made(results: list[str]):
    async def run() -> str:
        results.append(str(uuid.uuid4()))

        return results[-1]

    return run


def test_a_retry_gets_the_first_result_and_another_request_runs_again():
    company, key = uuid.uuid4(), uuid.uuid4()
    request = fingerprint("interview", {"job_description": "Backend", "language": None})
    other = fingerprint("interview", {"job_description": "Data", "language": None})
    results: list[str] = []

    async def scenario():
        try:
            name, seconds = slot(company, key, None, request)
            first = await once(name, seconds, request, made(results))
            again = await once(name, seconds, request, made(results))
            other_name, _ = slot(company, key, None, other)
            third = await once(other_name, seconds, other, made(results))
            ttl = await get_redis().ttl(name)

            return first, again, third, ttl
        finally:
            await get_redis().aclose()

    first, again, third, ttl = asyncio.run(scenario())

    assert first == again != third
    assert len(results) == 2
    assert 0 < ttl <= 15 * 60


def test_a_client_key_used_for_another_request_is_refused_and_a_failure_frees_it():
    company, key = uuid.uuid4(), uuid.uuid4()
    client_key = f"key-{uuid.uuid4()}"
    first, second = fingerprint("a"), fingerprint("b")

    async def failing() -> str:
        raise HTTPException(402, "No credits")

    async def scenario():
        try:
            name, seconds = slot(company, key, client_key, first)

            with pytest.raises(HTTPException):
                await once(name, seconds, first, failing)

            done = await once(name, seconds, first, made([]))

            with pytest.raises(HTTPException) as refused:
                await once(name, seconds, second, made([]))

            return done, refused.value.status_code
        finally:
            await get_redis().aclose()

    done, refused = asyncio.run(scenario())

    assert done and refused == 422
