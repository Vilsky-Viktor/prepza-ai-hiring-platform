"""AI calls traced to Langfuse (prepza_common.tracing): only with both keys, every LangChain call
of a traced run reporting to its one trace with its name and tags; and LangSmith configured
nowhere. Langfuse's callback is a fake here."""

import asyncio
import re
from contextlib import contextmanager
from pathlib import Path

import pytest
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.runnables import RunnableLambda
from prepza_common import tracing

ROOT = Path(__file__).resolve().parents[4]
TRACE_ID = re.compile(r"[0-9a-f]{32}")
# The Langfuse callbacks made.
MADE = []


class FakeHandler(BaseCallbackHandler):
    """Langfuse's LangChain callback: the trace it reports to and the runs reported."""

    run_inline = True

    def __init__(self, public_key, trace_context):
        self.trace_id = trace_context["trace_id"]
        self.runs = []
        MADE.append(self)

    def on_chain_start(self, serialized, inputs, **kwargs):
        self.runs.append(inputs)


@pytest.fixture
def langfuse(monkeypatch):
    """Langfuse set up, with its trace attributes recorded."""
    attributes = []

    @contextmanager
    def propagate(**kwargs):
        attributes.append(kwargs)
        yield

    MADE.clear()
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-test")
    monkeypatch.setattr(tracing, "client", lambda: None)
    monkeypatch.setattr(tracing, "CallbackHandler", FakeHandler)
    monkeypatch.setattr(tracing, "propagate_attributes", propagate)

    return attributes


def callbacks_seen(calls: int) -> list:
    """The handlers each of `calls` LangChain calls reported to."""
    seen = []

    def call(_, config):
        seen.append([h for h in config["callbacks"].handlers if isinstance(h, FakeHandler)])

    step = RunnableLambda(call)

    async def run():
        for number in range(calls):
            await step.ainvoke(number)

    asyncio.run(run())

    return seen


def test_a_traced_run_reports_every_call_to_its_one_trace_with_its_name_and_tags(langfuse):
    with tracing.traced_run("interview_generation", ["interview_generation", "gen-1"]) as trace:
        seen = callbacks_seen(2)

    assert TRACE_ID.fullmatch(trace)
    [handler] = MADE
    assert seen == [[handler], [handler]]
    assert (handler.trace_id, handler.runs) == (trace, [0, 1])
    assert langfuse == [
        {"trace_name": "interview_generation", "tags": ["interview_generation", "gen-1"]}
    ]
    # Calls after the run report to nothing.
    assert callbacks_seen(1) == [[]]


def test_the_same_seed_gives_the_same_trace(langfuse):
    with tracing.traced_run("interview_generation", [], seed="interview_generation:1") as first:
        pass

    with tracing.traced_run("interview_generation", [], seed="interview_generation:1") as again:
        pass

    with tracing.traced_run("interview_generation", [], seed="interview_generation:2") as other:
        pass

    assert first == again != other


def test_a_chat_answer_gets_a_trace_its_calls_report_to(langfuse):
    trace = tracing.new_trace_id()
    [handler] = tracing.traced(trace)["callbacks"]

    assert TRACE_ID.fullmatch(trace)
    assert handler.trace_id == trace
    assert tracing.traced(None) is None


@pytest.mark.parametrize("missing", ["LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"])
def test_without_both_keys_nothing_is_traced(langfuse, monkeypatch, missing):
    monkeypatch.delenv(missing)

    with tracing.traced_run("interview_generation", ["interview_generation"]) as trace:
        seen = callbacks_seen(1)

    assert trace is None
    assert seen == [[]]
    assert tracing.new_trace_id() is None
    assert (MADE, langfuse) == ([], [])


def test_the_host_is_langfuses_eu_cloud_unless_set(monkeypatch):
    made = {}
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-test")
    monkeypatch.delenv("LANGFUSE_HOST", raising=False)
    monkeypatch.setattr(tracing, "Langfuse", lambda **kwargs: made.update(kwargs))
    tracing.client.cache_clear()

    try:
        tracing.client()
    finally:
        tracing.client.cache_clear()

    assert made["host"] == "https://cloud.langfuse.com"


def test_nothing_configures_langsmith():
    """No service, compose file, setting or dependency sets up LangSmith or LangChain's own
    tracing; Langfuse is the only tracing."""
    files = [ROOT / ".env.example", ROOT / "evals" / "run.sh"]
    files += list((ROOT / "compose").glob("*.yml"))
    files += list(ROOT.glob("services/*/pyproject.toml"))
    files += list(ROOT.glob("services/*/app/**/*.py"))
    files += list(ROOT.glob("packages/common/src/**/*.py"))
    files.append(ROOT / "packages" / "common" / "pyproject.toml")
    pattern = re.compile(r"LANGSMITH_|LANGCHAIN_TRACING|LANGCHAIN_API_KEY|\"langsmith")

    found = [str(path) for path in files if pattern.search(path.read_text())]

    # The repo's files were found, so an empty list means none mention it.
    assert len(files) > 100
    assert found == []
