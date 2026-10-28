"""What the help chat's tests share: the knowledge rounds would send, Redis in memory, the pause
off, and the model's answers replaced."""

import pytest
from fake_redis import FakeRedis

from assistant.schemas.help_chat import HelpKnowledge
from assistant.services import help_answers, help_votes

KNOWLEDGE = "<platform_guide>A company can own up to 3 companies.</platform_guide>"
PAGE_GUIDE = "Pricing\nWhat credits cost.\nWhat you can do here:\n- Compare prices"
BODY = {"messages": [{"role": "user", "content": "How do I start?"}]}


def answering(*parts, usage=None, error=None, asked=None):
    """The model's answer: `parts`, its `usage`, then `error` raised when given. Each call's
    messages, trace and session go in `asked` when given."""

    async def stream(messages, used, trace_id=None, session_id=None):
        if asked is not None:
            asked.append((messages, trace_id, session_id))

        for part in parts:
            yield part

        if usage:
            used["usage"] = usage

        if error:
            raise error

    return stream


@pytest.fixture
def knowledge(monkeypatch):
    """Rounds' answer: the platform guide, and a page's guide for "pricing" only. The countries
    and pages asked for are kept."""
    asked = []

    async def fake(country, page):
        asked.append((country, page))

        return HelpKnowledge(
            knowledge=KNOWLEDGE, page_guide=PAGE_GUIDE if page == "pricing" else None
        )

    monkeypatch.setattr(help_answers, "help_knowledge", fake)

    return asked


@pytest.fixture
def help_redis(monkeypatch, knowledge):
    """Redis in memory, where the limits count; the pause off unless a test turns it on."""
    fake = FakeRedis()

    async def off(redis):
        return False

    monkeypatch.setattr("prepza_common.limits.pause.is_paused", off)
    monkeypatch.setattr(help_answers, "get_redis", lambda: fake)
    monkeypatch.setattr(help_votes, "get_redis", lambda: fake)

    return fake
