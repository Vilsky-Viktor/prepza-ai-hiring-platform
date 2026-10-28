"""Langfuse's traces deleted on time: every trace once TRACE_DELETE_AFTER_DAYS old (a daily
job), and a deleted account's own (the trace ids its service kept). Nothing happens while
Langfuse isn't set up. Deletion is Langfuse's to finish (within minutes); safe to repeat."""

import asyncio
import logging
import os
from collections.abc import AsyncIterator, Iterable
from datetime import UTC, datetime, timedelta

import httpx
from prepza_common.ai.tracing import EU_CLOUD, tracing_on
from prepza_common.config.constants import RETRY_AFTER
from prepza_common.http import http
from prepza_common.http.backoff import wait_seconds

from assistant.constants.trace_retention import (
    OBSERVATIONS_PATH,
    TRACE_ATTEMPTS,
    TRACE_DELETE_AFTER_DAYS,
    TRACE_DELETE_BATCH,
    TRACE_FIRST_WAIT_SECONDS,
    TRACE_MAX_WAIT_SECONDS,
    TRACE_PAGE,
    TRACE_RUN_SECONDS,
    TRACE_TIMEOUT_SECONDS,
    TRACES_PATH,
)

logger = logging.getLogger(__name__)
RETRIED = {429, 500, 502, 503, 504}


async def call(method: str, path: str, **kwargs) -> httpx.Response:
    """One call to Langfuse's public API with the project's keys, tried again on its rate limit
    or an outage (waiting at least its Retry-After, unless that's past TRACE_MAX_WAIT_SECONDS);
    a refusal raises."""
    url = (os.getenv("LANGFUSE_HOST") or EU_CLOUD).rstrip("/") + path
    auth = (os.environ["LANGFUSE_PUBLIC_KEY"], os.environ["LANGFUSE_SECRET_KEY"])

    for attempt in range(TRACE_ATTEMPTS):
        response = await http.get_client().request(
            method, url, auth=auth, timeout=TRACE_TIMEOUT_SECONDS, **kwargs
        )

        given = response.headers.get(RETRY_AFTER, "")
        wait = wait_seconds(TRACE_FIRST_WAIT_SECONDS, attempt)
        wait = max(int(given), wait) if given.isdigit() else wait

        if (
            response.status_code not in RETRIED
            or attempt == TRACE_ATTEMPTS - 1
            or wait > TRACE_MAX_WAIT_SECONDS
        ):
            response.raise_for_status()

            return response

        await asyncio.sleep(wait)

    raise RuntimeError("unreachable")


async def trace_pages_before(before: datetime) -> AsyncIterator[list[str]]:
    """The ids of traces that started before `before`, from their root observations, a page at
    a time."""
    cursor = None

    while True:
        params = {
            "isRootObservation": "true",
            "toStartTime": before.isoformat(),
            "fields": "core",
            "limit": TRACE_PAGE,
            **({"cursor": cursor} if cursor else {}),
        }
        body = (await call("GET", OBSERVATIONS_PATH, params=params)).json()
        yield [item["traceId"] for item in body.get("data", []) if item.get("traceId")]
        cursor = (body.get("meta") or {}).get("cursor")

        if not cursor:
            return


async def delete_traces(trace_ids: Iterable[str]) -> int:
    """Deletes these traces, TRACE_DELETE_BATCH a call; how many were asked to go."""
    ids = list(dict.fromkeys(trace_id for trace_id in trace_ids if trace_id))

    if not ids or not tracing_on():
        return 0

    for start in range(0, len(ids), TRACE_DELETE_BATCH):
        await call(
            "DELETE", TRACES_PATH, json={"traceIds": ids[start : start + TRACE_DELETE_BATCH]}
        )

    return len(ids)


async def delete_old_traces(now: datetime | None = None) -> int:
    """Every trace TRACE_DELETE_AFTER_DAYS old or more goes, a page at a time, so a run cut short
    keeps what it did; no page is started after TRACE_RUN_SECONDS, the rest left to the next
    run. How many were asked to go."""
    if not tracing_on():
        return 0

    before = (now or datetime.now(UTC)) - timedelta(days=TRACE_DELETE_AFTER_DAYS)
    stop = asyncio.get_running_loop().time() + TRACE_RUN_SECONDS
    seen: set[str] = set()

    async for page in trace_pages_before(before):
        fresh = [trace_id for trace_id in page if trace_id not in seen]
        seen.update(fresh)
        await delete_traces(fresh)

        if asyncio.get_running_loop().time() > stop:
            logger.info("Trace retention stopped for time; the rest goes in the next run")

            break

    logger.info("Asked Langfuse to delete %d traces past their retention", len(seen))

    return len(seen)
