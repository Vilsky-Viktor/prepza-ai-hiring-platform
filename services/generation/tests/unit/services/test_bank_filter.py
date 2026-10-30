"""The shared question bank's filter (services/bank_filter.py): its model is a fake here, and
its answers' quality is the eval's (evals/scripts/bank_filter_test.py)."""

import asyncio
import uuid
from types import SimpleNamespace

import pytest

from generation.integrations import library, llm
from generation.schemas.bank_filter import BankCandidate
from generation.services import bank_filter


class Filter:
    """The filter's model: says each question `identifies` (by its text), or raises for those in
    `fails`; records what it read."""

    def __init__(self, identifying=(), fails=()):
        self.identifying = set(identifying)
        self.fails = set(fails)
        self.read = []

    def with_structured_output(self, schema):
        return self

    async def ainvoke(self, messages):
        question = messages[1].content
        self.read.append(question)

        if any(text in question for text in self.fails):
            raise TimeoutError()

        return SimpleNamespace(identifies=any(text in question for text in self.identifying))


def candidate(text: str) -> BankCandidate:
    return BankCandidate(question_id=uuid.uuid4(), topic="Topic", text=text, options=["A", "B"])


@pytest.mark.parametrize(
    "text",
    [
        "Who answers billing@example.com?",
        "Where is https://wiki.example/guide kept?",
        "Which page at www.example.org is the start?",
    ],
)
def test_contact_details_keep_a_question_out_without_asking_the_model(text, monkeypatch):
    model = Filter()
    monkeypatch.setattr(llm, "get_bank_filter_llm", lambda: model)

    assert asyncio.run(bank_filter.is_general("Topic", text, ["A"])) is False
    assert model.read == []


def test_the_model_reads_the_topic_the_question_and_its_options_tagged_as_data(monkeypatch):
    model = Filter(identifying=["Halvo"])
    monkeypatch.setattr(llm, "get_bank_filter_llm", lambda: model)

    general = asyncio.run(bank_filter.is_general("Joins", "Which join keeps rows?", ["INNER"]))
    private = asyncio.run(bank_filter.is_general("Clients", "Who is Halvo's client?", ["X"]))

    assert (general, private) == (True, False)
    assert model.read[0] == (
        "<question>\nTopic: Joins\nQuestion: Which join keeps rows?\n- INNER\n</question>"
    )


def test_every_page_is_checked_and_saved_and_a_failed_check_waits_for_the_next_run(monkeypatch):
    pages = [[candidate("General?"), candidate("Acme's?"), candidate("Broken?")], []]
    asked, saved = [], []

    async def bank_candidates(limit, after=None):
        asked.append(after)

        return pages[len(asked) - 1]

    async def save_bank_checks(checks):
        saved.append([(check.text, check.passed) for check in checks])

    monkeypatch.setattr(llm, "get_bank_filter_llm", lambda: Filter(["Acme"], ["Broken"]))
    monkeypatch.setattr(library, "bank_candidates", bank_candidates)
    monkeypatch.setattr(library, "save_bank_checks", save_bank_checks)

    assert asyncio.run(bank_filter.check_all()) == 2
    assert saved == [[("General?", True), ("Acme's?", False)]]
    # The next page starts after the last one offered, the failed one included.
    assert asked == [None, pages[0][-1].question_id]


def test_a_run_stops_at_its_cap(monkeypatch):
    saved = []

    async def bank_candidates(limit, after=None):
        return [candidate(f"Q{index}?") for index in range(limit)]

    async def save_bank_checks(checks):
        saved.extend(checks)

    monkeypatch.setattr(bank_filter, "MAX_BANK_CHECKS", 4)
    monkeypatch.setattr(bank_filter, "BANK_FILTER_PAGE", 3)
    monkeypatch.setattr(llm, "get_bank_filter_llm", lambda: Filter())
    monkeypatch.setattr(library, "bank_candidates", bank_candidates)
    monkeypatch.setattr(library, "save_bank_checks", save_bank_checks)

    assert asyncio.run(bank_filter.check_all()) == 6
    assert len(saved) == 6


@pytest.mark.parametrize("paused, lock", [(True, "token"), (False, None)])
def test_no_run_during_the_pause_or_while_the_last_one_goes_on(paused, lock, monkeypatch):
    runs = []

    async def is_paused(redis):
        return paused

    async def acquire(redis, key, seconds):
        return lock

    async def check_all():
        runs.append("run")

        return 0

    monkeypatch.setattr(bank_filter, "get_redis", lambda: object())
    monkeypatch.setattr(bank_filter.pause, "is_paused", is_paused)
    monkeypatch.setattr(bank_filter.redis_lock, "acquire", acquire)
    monkeypatch.setattr(bank_filter, "check_all", check_all)

    asyncio.run(bank_filter.run())

    assert runs == []
