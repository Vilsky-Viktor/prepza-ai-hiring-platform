"""Questions asking the same thing are dropped by meaning; the comparison runs off the event loop."""

import asyncio

from app.services import dedupe


def test_a_text_too_close_to_a_kept_one_is_dropped_and_compared_in_a_thread(monkeypatch):
    vectors = [[1.0, 0.0], [1.0, 0.0], [0.0, 1.0]]
    threads = []

    async def embed(texts):
        return vectors

    async def to_thread(function, *args):
        threads.append(function.__name__)

        return function(*args)

    monkeypatch.setattr(dedupe, "embed", embed)
    monkeypatch.setattr(dedupe.asyncio, "to_thread", to_thread)

    kept = asyncio.run(dedupe.distinct_by_meaning(["a", "a again", "b"]))

    assert kept == [0, 2]
    assert threads == ["distinct"]


def test_the_first_ones_are_always_kept():
    assert dedupe.distinct([[1.0, 0.0], [1.0, 0.0]], keep_first=2) == [0, 1]
