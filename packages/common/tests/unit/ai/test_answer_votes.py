"""Votes on the chats' answers sent to Langfuse (prepza_common.ai.answer_votes): one score a trace, created or replaced to match the vote as it is when sent, deleted when cleared,
retried, sent within the vote's own request, and nothing at all without Langfuse's keys.
Langfuse itself is a fake here."""

import asyncio
import threading

import pytest
from langfuse.api.core.api_error import ApiError
from prepza_common.ai import answer_votes, tracing

TRACE = "a" * 32


class FakeScores:
    """Langfuse's scores API: scores by id (a score with a known id replaces it); the first
    `failures` calls fail."""

    def __init__(self):
        self.kept = {}
        self.failures = 0
        self.calls = []
        self.options = []
        self.release = None

    def fail(self):
        if self.release is not None:
            # Langfuse hanging until the test lets it go.
            self.release.wait()

        if self.failures:
            self.failures -= 1

            raise ConnectionError("Langfuse is down")

    def create(self, request, request_options=None):
        self.options.append(request_options)
        self.fail()
        self.calls.append("create")

        for score in request:
            self.kept[score.id] = score

    def delete(self, score_id, request_options=None):
        self.options.append(request_options)
        self.fail()
        self.calls.append("delete")

        if self.kept.pop(score_id, None) is None:
            raise ApiError(status_code=404, body="Not found")


class FakeLangfuse:
    def __init__(self):
        self.api = type("Api", (), {"scores": FakeScores()})()


@pytest.fixture
def langfuse(monkeypatch):
    fake = FakeLangfuse()
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-test")
    monkeypatch.setattr(tracing, "client", lambda: fake)
    monkeypatch.setattr(answer_votes, "FIRST_WAIT_SECONDS", 0)

    return fake.api.scores


def send(vote):
    async def current():
        return vote

    asyncio.run(answer_votes.send_vote(TRACE, current))


def test_a_vote_becomes_the_traces_user_vote_score(langfuse):
    send(answer_votes.UP)

    [score] = langfuse.kept.values()
    assert (score.id, score.trace_id, score.name, score.value, score.data_type) == (
        answer_votes.score_id(TRACE),
        TRACE,
        "user_vote",
        1,
        "NUMERIC",
    )


def test_a_changed_vote_replaces_the_same_score_and_a_cleared_one_deletes_it(langfuse):
    send(answer_votes.UP)
    send(answer_votes.DOWN)

    [score] = langfuse.kept.values()
    assert score.value == 0

    send(None)
    # Clearing again (a repeated request) finds nothing to delete, and that's fine.
    send(None)

    assert langfuse.kept == {}
    assert langfuse.calls == ["create", "create", "delete", "delete"]


def test_a_failed_send_is_retried_and_sends_the_vote_as_it_is_then(langfuse):
    langfuse.failures = 1
    votes = iter([answer_votes.UP, answer_votes.DOWN, answer_votes.DOWN])

    async def current():
        return next(votes)

    asyncio.run(answer_votes.send_vote(TRACE, current))

    [score] = langfuse.kept.values()
    assert score.value == 0
    # Langfuse's client doesn't retry on its own: the retries are ours alone.
    assert {option["max_retries"] for option in langfuse.options} == {0}


def test_after_the_last_try_the_vote_is_given_up_quietly(langfuse, caplog):
    langfuse.failures = answer_votes.SEND_ATTEMPTS

    send(answer_votes.UP)

    assert langfuse.kept == {}
    assert len([r for r in caplog.records if "Couldn't send a vote" in r.message]) == (
        answer_votes.SEND_ATTEMPTS
    )


def test_a_vote_changed_while_it_was_sent_is_sent_again_ending_with_the_latest(langfuse):
    votes = iter([answer_votes.UP, answer_votes.DOWN, answer_votes.DOWN, answer_votes.DOWN])

    async def current():
        return next(votes)

    asyncio.run(answer_votes.send_vote(TRACE, current))

    [score] = langfuse.kept.values()
    assert score.value == 0
    assert langfuse.calls == ["create", "create"]


def test_with_langfuse_a_vote_is_sent_before_the_request_ends(langfuse):
    async def current():
        return answer_votes.DOWN

    asyncio.run(answer_votes.mirror_vote(TRACE, current))

    assert [score.value for score in langfuse.kept.values()] == [0]


def test_a_hanging_langfuse_holds_the_request_no_longer_than_its_time(langfuse, monkeypatch):
    monkeypatch.setattr(answer_votes, "SEND_SECONDS", 0.05)
    langfuse.release = threading.Event()

    async def current():
        return answer_votes.UP

    async def scenario():
        try:
            await answer_votes.mirror_vote(TRACE, current)

            # Back while Langfuse still hasn't answered.
            return list(langfuse.calls)
        finally:
            # Let the hanging call go, or the test's loop would wait for its thread.
            langfuse.release.set()

    assert asyncio.run(scenario()) == []


def test_without_langfuses_keys_or_a_trace_nothing_is_sent(langfuse, monkeypatch):
    async def current():
        return answer_votes.UP

    async def scenario():
        await answer_votes.mirror_vote(None, current)
        monkeypatch.delenv("LANGFUSE_SECRET_KEY")
        await answer_votes.mirror_vote(TRACE, current)

    asyncio.run(scenario())

    assert langfuse.calls == []
