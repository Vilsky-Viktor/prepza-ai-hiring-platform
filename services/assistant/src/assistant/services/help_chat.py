from collections.abc import AsyncIterator

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.messages.ai import add_usage
from prepza_common.ai import ai_usage
from prepza_common.ai.ai_constants import Outcome
from prepza_common.ai.llm import estimated_input, estimated_tokens, latest_messages
from prepza_common.ai.scope import SCOPE_RULE
from prepza_common.ai.tracing import traced
from prepza_common.config.constants import LANGUAGES, OPERATOR
from prepza_common.i18n.text_language import text_language, word_hits
from prepza_common.limits.rate_limit import add_spent

from assistant.config import settings
from assistant.constants.chat_words import CHAT_WORDS
from assistant.constants.help_chat import (
    HELP_CHAT,
    HELP_HISTORY_CHARACTERS,
    HELP_HISTORY_MESSAGES,
    HELP_LANGUAGE_WORDS,
    HELP_SPEND_KEY,
    HelpRole,
)
from assistant.integrations import llm
from assistant.prompts.help_chat import HELP_SYSTEM, PAGE_CONTEXT, VISITOR_MESSAGE
from assistant.schemas.help_chat import HelpKnowledge, HelpMessage


def build_messages(
    conversation: list[HelpMessage], language: str, known: HelpKnowledge, page: str | None = None
) -> list[BaseMessage]:
    """The system prompt holds everything the chat may answer from (`known`, from site, in
    English), with the guide of the page the visitor asks on (`page`, its key) when it's a known
    one. The reply's language is chosen here: the visitor's question's own, else the page's.
    Each of the visitor's messages is tagged as data."""
    system = HELP_SYSTEM.format(
        page=PAGE_CONTEXT.format(key=page, guide=known.page_guide) if known.page_guide else "",
        email=OPERATOR["email"],
        knowledge=known.knowledge,
        language=LANGUAGES[reply_language(conversation[-1].content, language)],
        scope=SCOPE_RULE,
    )
    # The latest messages before the question (the last one, the user's), while they fit.
    before = conversation[-(HELP_HISTORY_MESSAGES + 1) : -1]
    earlier = latest_messages(
        [(item.role == HelpRole.USER, item.content) for item in before], HELP_HISTORY_CHARACTERS
    )
    earlier = [
        HumanMessage(content=VISITOR_MESSAGE.format(message=item.content))
        if isinstance(item, HumanMessage)
        else item
        for item in earlier
    ]
    question = HumanMessage(content=VISITOR_MESSAGE.format(message=conversation[-1].content))

    return [SystemMessage(content=system), *earlier, question]


def reply_language(question: str, page_language: str) -> str:
    """The language a reply is written in, chosen here, never by the model: the question's own
    when it clearly shows one (its script, or at least HELP_LANGUAGE_WORDS of a Latin-script
    language's chat words, more than of any other's and of the page's), else the page's."""
    found = text_language(question, fallback=page_language, unknown=page_language)

    if found not in CHAT_WORDS:
        return found

    hits = word_hits(question, CHAT_WORDS)
    best = max(hits, key=hits.get)
    others = [count for code, count in hits.items() if code != best]

    if hits[best] >= HELP_LANGUAGE_WORDS and hits[best] > max(others):
        return best

    return page_language


async def stream_reply(
    messages: list[BaseMessage],
    used: dict,
    trace_id: str | None = None,
    session_id: str | None = None,
) -> AsyncIterator[str]:
    """The answer's text as it comes; its usage metadata is kept in `used["usage"]`. `trace_id`:
    its Langfuse trace, when that's set up, in the chat's session (`session_id`)."""
    async for chunk in llm.get_help_llm().astream(messages, traced(trace_id, session_id)):
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
