"""Recording what AI calls used (prepza_common.ai_usage). A run is every model call made for one
action, such as a generation's pipeline run or one regenerated question: it records once per
model when it ends, and its calls that got no answer once more, estimated. A call inside a
nested run counts only for that one. With Langfuse set up, a run is also one trace there
(prepza_common.tracing): named by its action and tagged with it and its subject's id (the
generation's, for a generation), the same trace for every run of the same subject."""

import asyncio
from contextlib import asynccontextmanager
from contextvars import ContextVar

from langchain_core.callbacks import UsageMetadataCallbackHandler
from langchain_core.tracers.context import register_configure_hook
from prepza_common import ai_usage
from prepza_common.ai_constants import Outcome
from prepza_common.llm import estimated_input, estimated_tokens
from prepza_common.tracing import traced_run

from app.config.settings import settings
from app.constants.actions import EMBEDDINGS
from app.integrations import llm

# The run model calls are counted in; every model call made while it's set reports to it.
current: ContextVar["Run | None"] = ContextVar("ai_run", default=None)
register_configure_hook(current, inheritable=True)


class Run(UsageMetadataCallbackHandler):
    # Called in the event loop, not a thread: it only adds numbers.
    run_inline = True

    def __init__(self, action: str, company_id, user_id: str | None, subject_id) -> None:
        super().__init__()
        self.action = action
        self.who = {"company_id": company_id, "user_id": user_id}
        self.subject_id = subject_id
        self.outcome = Outcome.OK
        # Calls without an answer (yet): their model and estimated input tokens.
        self.unanswered = {}
        self.errors = []

    def on_chat_model_start(self, serialized, messages, *, run_id, **kwargs) -> None:
        params = kwargs.get("invocation_params") or {}
        model = params.get("model") or (kwargs.get("metadata") or {}).get("ls_model_name", "")
        self.unanswered[run_id] = (model, estimated_input(messages[0]))

    def on_llm_end(self, response, *, run_id, **kwargs) -> None:
        self.unanswered.pop(run_id, None)
        super().on_llm_end(response, run_id=run_id, **kwargs)

    def on_llm_error(self, error, *, run_id, **kwargs) -> None:
        self.errors.append(error)

    async def record(self) -> None:
        kept = {**self.who, "subject_id": self.subject_id}

        for model, usage in self.usage_metadata.items():
            await ai_usage.record(self.action, model, usage, outcome=self.outcome, **kept)

        unanswered = {}

        for model, tokens in self.unanswered.values():
            unanswered[model] = unanswered.get(model, 0) + tokens

        outcome = Outcome.FAILED if self.outcome == Outcome.OK else self.outcome

        for model, tokens in unanswered.items():
            usage = {"input_tokens": tokens}
            await ai_usage.record(self.action, model, usage, outcome=outcome, **kept)

        for error in self.errors:
            await ai_usage.provider_refused(error, self.action, **self.who)


@asynccontextmanager
async def ai_run(action: str, company_id=None, user_id: str | None = None, subject_id=None):
    """Counts the model calls made inside it for `action` and records them when it ends: cut
    when cancelled, failed when it raised. A provider's refusal of a call is recorded too."""
    run = Run(action, company_id, user_id, subject_id)
    token = current.set(run)
    subject = str(subject_id) if subject_id else None
    tags = [action, subject] if subject else [action]
    seed = f"{action}:{subject}" if subject else None

    try:
        with traced_run(action, tags, seed):
            yield run
    except asyncio.CancelledError:
        run.outcome = Outcome.CUT

        raise
    except Exception:
        run.outcome = Outcome.FAILED

        raise
    finally:
        current.reset(token)
        await run.record()


def cut() -> None:
    """The current run stopped short: its time ran out."""
    run = current.get()

    if run is not None:
        run.outcome = Outcome.CUT


async def embed(texts: list[str]) -> list[list[float]]:
    """The texts' embeddings, recorded for the current run's company and user. Embeddings report
    no usage, so their input is estimated."""
    run = current.get()
    who = run.who if run else {}
    subject_id = run.subject_id if run else None
    usage = {"input_tokens": sum(estimated_tokens(text) for text in texts)}
    outcome = Outcome.FAILED

    try:
        vectors = await llm.get_embeddings().aembed_documents(texts)
        outcome = Outcome.OK

        return vectors
    except asyncio.CancelledError:
        outcome = Outcome.CUT

        raise
    except Exception as error:
        await ai_usage.provider_refused(error, EMBEDDINGS, **who)

        raise
    finally:
        kept = {**who, "subject_id": subject_id}
        await ai_usage.record(EMBEDDINGS, settings.embedding_model, usage, outcome=outcome, **kept)
