"""Langfuse's traces deleted on time: every trace once TRACE_DELETE_AFTER_DAYS old (a daily
job), and a deleted account's own (the trace ids its service kept). Nothing happens while
Langfuse isn't set up. Deletion is Langfuse's to finish (within minutes); safe to repeat."""

import asyncio
import logging
import os
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta

import httpx
from prepza_common import http
from prepza_common.backoff import wait_seconds
from prepza_common.constants import RETRY_AFTER
from prepza_common.trace_constants import (
    OBSERVATIONS_PATH,
    TRACE_ATTEMPTS,
    TRACE_DELETE_AFTER_DAYS,
    TRACE_DELETE_BATCH,
    TRACE_FIRST_WAIT_SECONDS,
    TRACE_PAGE,
    TRACE_TIMEOUT_SECONDS,
    TRACES_PATH,
)
from prepza_common.tracing import EU_CLOUD, tracing_on

logger = logging.getLogger(__name__)
RETRIED = {429, 500, 502, 503, 504}


async def call(method: str, path: str, **kwargs) -> httpx.Response:
    """One call to Langfuse's public API with the project's keys, tried again on its rate limit
    or an outage (waiting at least its Retry-After); a refusal raises."""
    url = (os.getenv("LANGFUSE_HOST") or EU_CLOUD).rstrip("/") + path
    auth = (os.environ["LANGFUSE_PUBLIC_KEY"], os.environ["LANGFUSE_SECRET_KEY"])

    for attempt in range(TRACE_ATTEMPTS):
        response = await http.get_client().request(
            method, url, auth=auth, timeout=TRACE_TIMEOUT_SECONDS, **kwargs
        )

        if response.status_code not in RETRIED or attempt == TRACE_ATTEMPTS - 1:
            response.raise_for_status()

            return response

        given = response.headers.get(RETRY_AFTER, "")
        wait = wait_seconds(TRACE_FIRST_WAIT_SECONDS, attempt)
        await asyncio.sleep(max(int(given), wait) if given.isdigit() else wait)

    raise RuntimeError("unreachable")


async def trace_ids_before(before: datetime) -> list[str]:
    """The ids of traces that started before `before`, from their root observations, page by
    page."""
    found: list[str] = []
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
        found += [item["traceId"] for item in body.get("data", []) if item.get("traceId")]
        cursor = (body.get("meta") or {}).get("cursor")

        if not cursor:
            return list(dict.fromkeys(found))


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
    """Every trace TRACE_DELETE_AFTER_DAYS old or more goes; how many."""
    if not tracing_on():
        return 0

    before = (now or datetime.now(UTC)) - timedelta(days=TRACE_DELETE_AFTER_DAYS)
    deleted = await delete_traces(await trace_ids_before(before))
    logger.info("Asked Langfuse to delete %d traces past their retention", deleted)

    return deleted
