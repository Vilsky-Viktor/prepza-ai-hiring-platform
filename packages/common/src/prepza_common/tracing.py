"""AI calls traced to Langfuse through its LangChain callback. On only when LANGFUSE_PUBLIC_KEY
and LANGFUSE_SECRET_KEY are set (LANGFUSE_HOST: Langfuse's EU cloud unless set); nothing goes
anywhere else (LangSmith isn't configured). Needs the package's `langfuse` extra."""

import os
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from functools import cache

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.tracers.context import register_configure_hook
from langfuse import Langfuse, propagate_attributes
from langfuse.langchain import CallbackHandler

EU_CLOUD = "https://cloud.langfuse.com"

# The traced run's handler; every LangChain call made while it's set reports to it.
_run_handler: ContextVar[BaseCallbackHandler | None] = ContextVar("langfuse_run", default=None)
register_configure_hook(_run_handler, inheritable=True)


def tracing_on() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))


@cache
def client() -> Langfuse:
    return Langfuse(
        public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
        secret_key=os.environ["LANGFUSE_SECRET_KEY"],
        host=os.getenv("LANGFUSE_HOST") or EU_CLOUD,
        # Which environment the traces are from, like Sentry's (SENTRY_ENVIRONMENT).
        environment=os.getenv("LANGFUSE_ENVIRONMENT", "production"),
    )


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


def traced(trace_id: str | None) -> dict | None:
    """The config a model call reports to the trace with; None without one."""
    if trace_id is None:
        return None

    return {"callbacks": [handler(trace_id)]}


@contextmanager
def traced_run(name: str, tags: list[str], seed: str | None = None) -> Iterator[str | None]:
    """Every LangChain call made inside (LangGraph runs too) reports to one trace named `name`,
    tagged with `tags`: ids only, never names, emails or a job's text. The same seed gives the
    same trace. Yields its id; None when Langfuse isn't set up."""
    trace_id = new_trace_id(seed)

    if trace_id is None:
        yield None

        return

    token = _run_handler.set(handler(trace_id))

    try:
        with propagate_attributes(trace_name=name, tags=tags):
            yield trace_id
    finally:
        _run_handler.reset(token)
