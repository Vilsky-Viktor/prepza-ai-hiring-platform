"""Chat answers traced to Langfuse and votes on them sent there (prepza_common.answer_votes): one
score a trace, created or replaced to match the vote as it is when sent, deleted when cleared,
retried, and nothing at all without Langfuse's keys. Langfuse itself is a fake here."""

import asyncio

import pytest
from langfuse.api.core.api_error import ApiError
from prepza_common import answer_votes

TRACE = "a" * 32


class FakeScores:
    """Langfuse's scores API: scores by id (a score with a known id replaces it); the first
    `failures` calls fail."""

    def __init__(self):
        self.kept = {}
        self.failures = 0
        self.calls = []

    def fail(self):
        if self.failures:
            self.failures -= 1

            raise ConnectionError("Langfuse is down")

    def create(self, request):
        self.fail()
        self.calls.append("create")

        for score in request:
            self.kept[score.id] = score

    def delete(self, score_id):
        self.fail()
        self.calls.append("delete")

        if self.kept.pop(score_id, None) is None:
            raise ApiError(status_code=404, body="Not found")


class FakeLangfuse:
    def __init__(self):
        self.api = type("Api", (), {"scores": FakeScores()})()

    def create_trace_id(self):
        return TRACE


@pytest.fixture
def langfuse(monkeypatch):
    fake = FakeLangfuse()
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-test")
    monkeypatch.setattr(answer_votes, "_client", lambda: fake)
    monkeypatch.setattr(answer_votes, "FIRST_WAIT_SECONDS", 0)
    monkeypatch.setattr(answer_votes, "_locks", {})

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
    langfuse.failures = 2
    votes = iter([answer_votes.UP, answer_votes.UP, answer_votes.DOWN])

    async def current():
        return next(votes)

    asyncio.run(answer_votes.send_vote(TRACE, current))

    [score] = langfuse.kept.values()
    assert score.value == 0


def test_after_the_last_try_the_vote_is_given_up_quietly(langfuse, caplog):
    langfuse.failures = answer_votes.SEND_ATTEMPTS

    send(answer_votes.UP)

    assert langfuse.kept == {}
    assert len([r for r in caplog.records if "Couldn't send a vote" in r.message]) == (
        answer_votes.SEND_ATTEMPTS
    )


def test_quick_changes_are_sent_one_after_another_ending_with_the_latest(langfuse):
    state = {"vote": answer_votes.UP}

    async def current():
        return state["vote"]

    async def both():
        first = asyncio.create_task(answer_votes.send_vote(TRACE, current))
        state["vote"] = answer_votes.DOWN
        second = asyncio.create_task(answer_votes.send_vote(TRACE, current))
        await asyncio.gather(first, second)

    asyncio.run(both())

    [score] = langfuse.kept.values()
    assert score.value == 0


def test_with_langfuse_a_vote_goes_in_the_background_and_answers_get_traces(langfuse):
    async def current():
        return answer_votes.DOWN

    async def scenario():
        answer_votes.mirror_vote(TRACE, current)
        await asyncio.gather(*answer_votes._sending)

    asyncio.run(scenario())

    assert answer_votes.new_trace_id() == TRACE
    [handler] = answer_votes.traced(TRACE)["callbacks"]
    assert [score.value for score in langfuse.kept.values()] == [0]
    assert answer_votes.traced(None) is None
    assert handler is not None


def test_without_langfuses_keys_or_a_trace_nothing_is_traced_or_sent(langfuse, monkeypatch):
    async def current():
        return answer_votes.UP

    async def scenario():
        answer_votes.mirror_vote(None, current)
        monkeypatch.delenv("LANGFUSE_SECRET_KEY")
        answer_votes.mirror_vote(TRACE, current)
        await asyncio.sleep(0)

    asyncio.run(scenario())

    assert answer_votes.new_trace_id() is None
    assert langfuse.calls == []
