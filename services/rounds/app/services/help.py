from collections.abc import AsyncIterator

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.messages.ai import add_usage
from prepza_common import ai_usage, memory_cache
from prepza_common.ai_constants import Outcome
from prepza_common.answer_votes import traced
from prepza_common.constants import DEFAULT_LANGUAGE, LANGUAGES
from prepza_common.limit_schemas import BudgetOut
from prepza_common.limits import limit, question_seconds
from prepza_common.llm import estimated_input, estimated_tokens, latest_messages
from prepza_common.rate_limit import add_spent
from prepza_common.scope import SCOPE_RULE

from app.config.settings import settings
from app.constants.help import (
    GUIDE_CACHE_SECONDS,
    HELP_ALL_KEY,
    HELP_CHAT,
    HELP_HISTORY_CHARACTERS,
    HELP_HISTORY_MESSAGES,
    HELP_SPEND_KEY,
    HelpRole,
)
from app.constants.legal import COMPANY
from app.helpers.help import knowledge
from app.helpers.page_guides import guide_text, page_guide
from app.integrations import billing, llm
from app.integrations.redis import get_redis
from app.prompts.help import HELP_SYSTEM, PAGE_CONTEXT
from app.schemas.help import HelpMessage


async def guide_limits(redis) -> dict:
    """The limits the platform guide names, as they are now, so it never contradicts the site."""
    return {
        "max_companies": await limit(redis, "MAX_OWNED_COMPANIES"),
        "interviews_per_day": await limit(redis, "INTERVIEWS_PER_DAY"),
        "interviews_per_day_unpaid": await limit(redis, "INTERVIEWS_PER_DAY_UNPAID"),
        "waiting_interviews": await limit(redis, "MAX_INTERVIEWS_WITHOUT_CANDIDATES"),
        "waiting_interviews_unpaid": await limit(redis, "MAX_INTERVIEWS_WITHOUT_CANDIDATES_UNPAID"),
        "seconds_basic": await question_seconds(redis, "basic"),
        "seconds_medium": await question_seconds(redis, "medium"),
        "seconds_hard": await question_seconds(redis, "hard"),
    }


async def build_messages(
    conversation: list[HelpMessage], language: str, catalog: dict | None, page: str | None = None
) -> list[BaseMessage]:
    """The system prompt holds everything the chat may answer from, in English, with the guide
    of the page the visitor asks on (`page`, its key) when it's a known one; it replies in the
    page's language."""
    limits = await guide_limits(get_redis())
    guide = page_guide(page, DEFAULT_LANGUAGE) if page else None
    system = HELP_SYSTEM.format(
        page=PAGE_CONTEXT.format(key=page, guide=guide_text(guide)) if guide else "",
        email=COMPANY["email"],
        knowledge=knowledge(DEFAULT_LANGUAGE, catalog, limits),
        language=LANGUAGES[language],
        scope=SCOPE_RULE,
    )
    # The latest messages before the question (the last one, the user's), while they fit.
    before = conversation[-(HELP_HISTORY_MESSAGES + 1) : -1]
    earlier = latest_messages(
        [(item.role == HelpRole.USER, item.content) for item in before], HELP_HISTORY_CHARACTERS
    )

    return [SystemMessage(content=system), *earlier, HumanMessage(content=conversation[-1].content)]


async def stream_reply(
    messages: list[BaseMessage], used: dict, trace_id: str | None = None
) -> AsyncIterator[str]:
    """The answer's text as it comes; its usage metadata is kept in `used["usage"]`. `trace_id`:
    its Langfuse trace, when that's set up."""
    async for chunk in llm.get_help_llm().astream(messages, traced(trace_id)):
        if chunk.usage_metadata:
            used["usage"] = add_usage(used.get("usage"), chunk.usage_metadata)

        if chunk.content:
            yield chunk.content


async def record_answer(
    redis,
    messages: list[BaseMessage],
    reply: str,
    usage: dict | None,
    outcome: Outcome,
    user_id: str | None,
) -> None:
    """However an answer ended (written, failed or cut short), records its AI call and adds its
    tokens to the day's budget: estimated when the model reported none. Going over the budget
    refuses the next question, not this one; with Redis down, the spending is lost rather than
    the answer."""
    if not usage:
        usage = {
            "input_tokens": estimated_input(messages),
            "output_tokens": estimated_tokens(reply),
        }

    await ai_usage.record(HELP_CHAT, settings.help_model, usage, user_id=user_id, outcome=outcome)
    tokens = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
    await add_spent(redis, HELP_SPEND_KEY, tokens, "HELP_TOKENS_PER_DAY", user_id=user_id)


async def budgets(redis) -> list[BudgetOut]:
    """How much of the help chat's shared daily budgets is used today."""
    tokens = int(await redis.get(HELP_SPEND_KEY) or 0)
    calls = int(await redis.get(HELP_ALL_KEY) or 0)

    return [
        BudgetOut(
            name="HELP_TOKENS_PER_DAY",
            used=tokens,
            limit=await limit(redis, "HELP_TOKENS_PER_DAY"),
            unit="tokens",
        ),
        BudgetOut(
            name="HELP_DAILY_LIMIT",
            used=calls,
            limit=await limit(redis, "HELP_DAILY_LIMIT"),
            unit="calls",
        ),
    ]


async def platform_guide(language: str) -> str:
    """The help chat's knowledge with the FAQ in `language`, kept a while in this process."""
    key = f"help:guide:{language}"
    found = memory_cache.get(key)

    if found is None:
        catalog = await billing.catalog()
        found = knowledge(language, catalog, await guide_limits(get_redis()))

        # Without billing's prices, it's made again next time.
        if catalog is not None:
            memory_cache.put(key, found, GUIDE_CACHE_SECONDS)

    return found
