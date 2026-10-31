"""AI calls traced to Langfuse through its LangChain callback. On only when LANGFUSE_PUBLIC_KEY
and LANGFUSE_SECRET_KEY are set (LANGFUSE_HOST: Langfuse's EU cloud unless set); nothing goes
anywhere else (LangSmith isn't configured). Personal data is masked before it's sent: emails,
URLs' paths (tokens), `name` and `email` fields, and the names a caller hides (`hiding`). Needs
the package's `langfuse` extra."""

import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from functools import cache

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.tracers.context import register_configure_hook
from langfuse import Langfuse, propagate_attributes
from langfuse.langchain import CallbackHandler
from testee_common.observability.scrub import scrub_people

EU_CLOUD = "https://cloud.langfuse.com"

# The traced run's handler; every LangChain call made while it's set reports to it.
_run_handler: ContextVar[BaseCallbackHandler | None] = ContextVar("langfuse_run", default=None)
register_configure_hook(_run_handler, inheritable=True)
# Words masked in what the current calls report (a user's own name in the instructions).
_hidden: ContextVar[tuple[str, ...]] = ContextVar("langfuse_hidden", default=())


def tracing_on() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))


@cache
def client() -> Langfuse:
    return Langfuse(
        public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
        secret_key=os.environ["LANGFUSE_SECRET_KEY"],
        host=os.getenv("LANGFUSE_HOST") or EU_CLOUD,
        # Which environment the traces are from, the same ENVIRONMENT Sentry reports.
        environment=os.getenv("ENVIRONMENT", "production"),
        mask=mask,
    )


def mask(*, data, **kwargs):
    """What Langfuse sends of a call's input, output and metadata: without personal data."""
    return scrub_people(data, _hidden.get())


@contextmanager
def hiding(*words: str | None) -> Iterator[None]:
    """Masks `words` (empty ones skipped) in what the calls made inside report, also as JSON
    writes them (non-ASCII letters escaped)."""
    hidden = {form for word in words if word for form in (word, json.dumps(word)[1:-1])}
    token = _hidden.set(tuple(hidden))

    try:
        yield
    finally:
        _hidden.reset(token)


def new_trace_id(seed: str | None = None) -> str | None:
    """A new Langfuse trace (the same one for the same seed); None when Langfuse isn't set up."""
    if not tracing_on():
        return None

    return Langfuse.create_trace_id(seed=seed)


def handler(trace_id: str) -> CallbackHandler:
    """The callback that reports model calls to the trace."""
    # The handler reports through the client made with these keys.
    client()

    return CallbackHandler(
        public_key=os.environ["LANGFUSE_PUBLIC_KEY"], trace_context={"trace_id": trace_id}
    )


def traced(trace_id: str | None, session_id: str | None = None) -> dict | None:
    """The config a model call reports to the trace with, in the session `session_id` (a
    conversation's id: its traces are grouped there); None without a trace."""
    if trace_id is None:
        return None

    config = {"callbacks": [handler(trace_id)]}

    if session_id:
        config["metadata"] = {"langfuse_session_id": session_id}

    return config


def traced_call(
    name: str, tags: list[str], seed: str, model: str, usage: dict, cost: float | None, output
) -> None:
    """Reports one model call made outside LangChain (a Batch API request) to the trace of
    `seed`, named `name` and tagged with `tags` (ids only), with its tokens (cached input apart)
    and its cost. Nothing without Langfuse."""
    trace_id = new_trace_id(seed)

    if trace_id is None:
        return

    cached = (usage.get("input_token_details") or {}).get("cache_read", 0) or 0
    tokens = {
        "input": usage.get("input_tokens", 0) - cached,
        "input_cache_read": cached,
        "output": usage.get("output_tokens", 0),
    }

    with propagate_attributes(trace_name=name, tags=tags):
        client().start_observation(
            trace_context={"trace_id": trace_id},
            name=name,
            as_type="generation",
            model=model,
            output=output,
            usage_details=tokens,
            cost_details=None if cost is None else {"total": cost},
        ).end()


@contextmanager
def traced_run(
    name: str, tags: list[str], seed: str | None = None, session_id: str | None = None
) -> Iterator[str | None]:
    """Every LangChain call made inside (LangGraph runs too) reports to one trace named `name`,
    tagged with `tags`: ids only, never names, emails or a job's text, in the session
    `session_id` when given (a conversation's id). The same seed gives the same trace. Yields
    its id; None when Langfuse isn't set up."""
    trace_id = new_trace_id(seed)

    if trace_id is None:
        yield None

        return

    token = _run_handler.set(handler(trace_id))

    try:
        with propagate_attributes(trace_name=name, tags=tags, session_id=session_id):
            yield trace_id
    finally:
        _run_handler.reset(token)
