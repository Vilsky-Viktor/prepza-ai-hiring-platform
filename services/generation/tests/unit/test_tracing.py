"""Generation's AI runs traced to Langfuse when its keys are set: one trace a run with every
model call of it, named by its action and tagged with its subject's id (the generation's), no
company, user or text; the same trace for every run of a generation; nothing without the keys.
Langfuse's callback is a fake here."""

import asyncio
import uuid
from contextlib import contextmanager

import pytest
from langchain_core.callbacks import BaseCallbackHandler
from langgraph.graph import END, START, StateGraph
from prepza_common import tracing
from typing_extensions import TypedDict

from app.constants.actions import INTERVIEW_GENERATION
from app.integrations import usage
from tests.unit.fake_ai import Chat, reply

COMPANY_ID = uuid.uuid4()
GENERATION_ID = uuid.uuid4()
JOB_TEXT = "Senior engineer at Acme Corp, contact jane@example.com"


class FakeHandler(BaseCallbackHandler):
    """Langfuse's LangChain callback: the trace it reports to and the model calls reported."""

    run_inline = True

    def __init__(self, public_key, trace_context):
        self.trace_id = trace_context["trace_id"]
        self.calls = 0

    def on_chat_model_start(self, serialized, messages, **kwargs):
        self.calls += 1


@pytest.fixture
def langfuse(monkeypatch):
    """Langfuse set up: the handlers made and the trace attributes given."""
    seen = {"handlers": [], "attributes": []}

    def make(public_key, trace_context):
        handler = FakeHandler(public_key, trace_context)
        seen["handlers"].append(handler)

        return handler

    @contextmanager
    def propagate(**kwargs):
        seen["attributes"].append(kwargs)
        yield

    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-test")
    monkeypatch.setattr(tracing, "client", lambda: None)
    monkeypatch.setattr(tracing, "CallbackHandler", make)
    monkeypatch.setattr(tracing, "propagate_attributes", propagate)

    return seen


def generate(calls: int) -> None:
    """One generation run making `calls` model calls with the job's text."""
    chat = Chat(replies=[reply(10, 2) for _ in range(calls)])

    async def run():
        who = {"company_id": COMPANY_ID, "user_id": "owner-uid", "subject_id": GENERATION_ID}

        async with usage.ai_run(INTERVIEW_GENERATION, **who):
            for _ in range(calls):
                await chat.ainvoke(JOB_TEXT)

    asyncio.run(run())


def test_a_generation_run_is_one_trace_tagged_with_the_generation_id_only(langfuse, events):
    generate(3)

    [handler] = langfuse["handlers"]
    assert handler.calls == 3
    [attributes] = langfuse["attributes"]
    assert attributes == {
        "trace_name": INTERVIEW_GENERATION,
        "tags": [INTERVIEW_GENERATION, str(GENERATION_ID)],
        "session_id": None,
    }
    tags = " ".join(attributes["tags"])
    assert str(COMPANY_ID) not in tags
    assert "owner-uid" not in tags
    assert "Acme" not in tags and "jane@example.com" not in tags


def test_a_langgraph_runs_model_calls_report_to_the_runs_trace(langfuse, events):
    class State(TypedDict):
        text: str

    chat = Chat(replies=[reply(10, 2), reply(10, 2)])

    async def node(state):
        await chat.ainvoke(state["text"])

        return {}

    graph = StateGraph(State)
    graph.add_node("first", node)
    graph.add_node("second", node)
    graph.add_edge(START, "first")
    graph.add_edge("first", "second")
    graph.add_edge("second", END)

    async def run():
        async with usage.ai_run(INTERVIEW_GENERATION, subject_id=GENERATION_ID):
            await graph.compile().ainvoke({"text": JOB_TEXT})

    asyncio.run(run())

    [handler] = langfuse["handlers"]
    assert handler.calls == 2


def test_a_generations_runs_before_and_after_review_share_one_trace(langfuse, events):
    generate(1)
    generate(1)

    first, resumed = langfuse["handlers"]
    assert first.trace_id == resumed.trace_id


def test_without_langfuses_keys_nothing_is_traced(langfuse, events, monkeypatch):
    monkeypatch.delenv("LANGFUSE_SECRET_KEY")

    generate(1)

    assert langfuse == {"handlers": [], "attributes": []}
