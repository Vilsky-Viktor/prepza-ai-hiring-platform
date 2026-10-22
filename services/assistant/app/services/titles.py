import logging

from prepza_common import ai_usage
from prepza_common.ai_constants import Outcome
from prepza_common.llm import estimated_input
from prepza_common.tracing import traced_run

from app.config.settings import settings
from app.constants.ai_usage import TITLE_ACTION
from app.constants.titles import TITLE_SOURCE_CHARACTERS
from app.helpers.history import history
from app.helpers.titles import clean_title, should_title, title_prompt
from app.integrations import llm
from app.integrations.redis import get_redis
from app.models.answers import Turn
from app.services import limits
from app.storage import conversations, messages

logger = logging.getLogger(__name__)


async def refresh(turn: Turn) -> str | None:
    """A new title for the conversation when it's time (should_title), written by the cheap
    model call; its tokens count against the budgets. None when it isn't time or the call
    failed, and the old title stays."""
    if not should_title(await messages.count_questions(turn.conversation_id)):
        return None

    earlier = await messages.recent(turn.conversation_id, 20)
    prompt = title_prompt(history(earlier, TITLE_SOURCE_CHARACTERS), turn.language)
    who = {"company_id": turn.company_id, "user_id": turn.user_id}
    recorded = {**who, "subject_id": turn.conversation_id}

    try:
        # Its own trace in Langfuse when that's set up.
        with traced_run(TITLE_ACTION, [TITLE_ACTION, str(turn.conversation_id)]):
            reply = await llm.get_title_model().ainvoke(prompt)
    except Exception as failure:  # noqa: BLE001 - logged by its type only
        logger.error("A conversation's title failed: %s", type(failure).__name__)
        await ai_usage.provider_refused(failure, TITLE_ACTION, **who)
        usage = {"input_tokens": estimated_input(prompt)}
        model = settings.title_model
        await ai_usage.record(TITLE_ACTION, model, usage, outcome=Outcome.FAILED, **recorded)

        return None

    usage = reply.usage_metadata or {}
    await ai_usage.record(TITLE_ACTION, settings.title_model, usage, **recorded)
    tokens = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
    await limits.record(get_redis(), turn.user_id, turn.company_id, tokens)
    title = clean_title(reply.text)

    if title:
        await conversations.set_title(turn.conversation_id, title)

    return title
