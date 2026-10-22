"""Langfuse's traces deleted on time (prepza_common.trace_retention), against a fake Langfuse."""

import asyncio
import json
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from prepza_common import http, trace_retention

NOW = datetime(2026, 10, 22, tzinfo=UTC)


@pytest.fixture
def langfuse(monkeypatch):
    """Langfuse set up, answering two pages of old root observations (a trace seen twice),
    a rate limit once, and recording what it was asked to delete."""
    state = {"deleted": [], "asked": [], "busy": 1, "slept": []}
    pages = {
        None: {"data": [{"traceId": "t1"}, {"traceId": "t2"}], "meta": {"cursor": "c2"}},
        "c2": {"data": [{"traceId": "t2"}, {"traceId": "t3"}], "meta": {}},
    }

    def answer(request: httpx.Request) -> httpx.Response:
        state["asked"].append(request)
        assert request.headers["Authorization"].startswith("Basic ")

        if request.method == "GET":
            return httpx.Response(200, json=pages[request.url.params.get("cursor")])

        if state["busy"]:
            state["busy"] -= 1

            return httpx.Response(429, headers={"Retry-After": "7"})

        state["deleted"].append(json.loads(request.content)["traceIds"])

        return httpx.Response(200, json={"message": "ok"})

    async def sleep(seconds):
        state["slept"].append(seconds)

    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-test")
    monkeypatch.setattr(
        http, "get_client", lambda: httpx.AsyncClient(transport=httpx.MockTransport(answer))
    )
    monkeypatch.setattr(trace_retention.asyncio, "sleep", sleep)

    return state


def test_traces_a_day_short_of_30_days_old_are_found_page_by_page_and_deleted(langfuse):
    assert asyncio.run(trace_retention.delete_old_traces(NOW)) == 3

    first = langfuse["asked"][0].url.params
    assert first["isRootObservation"] == "true"
    assert first["toStartTime"] == (NOW - timedelta(days=29)).isoformat()
    # Langfuse's rate limit was waited out, at least as long as it asked.
    assert langfuse["slept"] == [7]
    assert langfuse["deleted"] == [["t1", "t2", "t3"]]


def test_an_accounts_traces_go_in_batches_and_none_is_no_call(langfuse, monkeypatch):
    monkeypatch.setattr(trace_retention, "TRACE_DELETE_BATCH", 2)
    langfuse["busy"] = 0

    assert asyncio.run(trace_retention.delete_traces(["a", "b", "a", None, "c"])) == 3
    assert asyncio.run(trace_retention.delete_traces([])) == 0
    assert langfuse["deleted"] == [["a", "b"], ["c"]]


def test_without_langfuse_nothing_is_asked(langfuse, monkeypatch):
    monkeypatch.delenv("LANGFUSE_SECRET_KEY")

    assert asyncio.run(trace_retention.delete_old_traces(NOW)) == 0
    assert asyncio.run(trace_retention.delete_traces(["a"])) == 0
    assert langfuse["asked"] == []
