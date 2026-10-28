import logging
import uuid
from collections.abc import AsyncIterator

import anyio
import httpx
from fastapi import Request
from langchain_core.messages import BaseMessage
from prepza_common.ai import ai_cap
from prepza_common.ai.ai_constants import Outcome
from prepza_common.ai.ai_usage import provider_refused
from prepza_common.ai.secrets_check import secret_in
from prepza_common.ai.tracing import new_trace_id
from prepza_common.auth.human_check import require_human
from prepza_common.auth.user import User
from prepza_common.events.analytics import track
from prepza_common.http.client_ip import limit_address
from prepza_common.http.sse import sse_event
from prepza_common.i18n.i18n import translate
from prepza_common.limits.pause import refuse_if_paused
from prepza_common.limits.rate_limit import hit, spend

from assistant.config import settings
from assistant.constants.chat import CHAT_FAILED
from assistant.constants.help_chat import HELP_ALL_KEY, HELP_CHAT, HELP_SPEND_KEY, HelpRole
from assistant.helpers.help_replies import (
    help_signing_key,
    reply_signature,
    trusted,
    vote_signature,
)
from assistant.helpers.help_sign_in import secret_reply, with_sign_in
from assistant.integrations.help_knowledge import help_knowledge
from assistant.integrations.redis import get_redis
from assistant.schemas.help_chat import HelpChatRequest
from assistant.services.help_chat import build_messages, record_answer, stream_reply
from assistant.services.turns import refuse_if_busy, running

logger = logging.getLogger(__name__)


async def start(
    body: HelpChatRequest,
    request: Request,
    user: User | None,
    country: str | None,
    language: str,
) -> AsyncIterator[str]:
    """Checks a question before anything streams (plain HTTP errors): the pause, the human
    check, the limits; then returns the answer's events. A conversation with a secret in it is
    answered at once with a fixed reply, before anything else, and nothing of it is used."""
    if secret_in([message.content for message in body.messages]) is not None:
        return secret_reply(language)

    refuse_if_busy()
    redis = get_redis()
    user_id = user.uid if user else None
    await refuse_if_paused(redis, HELP_CHAT, user_id=user_id)
    conversation = trusted(body.messages, help_signing_key(settings.service_secret))

    # A visitor shows they're a person once, until the chat has a reply: the chat has no id to
    # remember it by, a signed reply came only after the check, and it shows nothing to most.
    if user is None and not any(item.role == HelpRole.ASSISTANT for item in conversation):
        await require_human(request, settings.turnstile_secret_key)

    if user:
        await hit(redis, f"rate:help:{user.uid}", "HELP_USER_LIMIT", user_id=user_id)

    await hit(redis, f"rate:help:ip:{limit_address(request)}", "HELP_IP_LIMIT")
    await hit(redis, HELP_ALL_KEY, "HELP_DAILY_LIMIT", user_id=user_id)
    # The day's token budget, checked before the answer and counted after it.
    await spend(redis, HELP_SPEND_KEY, 0, "HELP_TOKENS_PER_DAY", user_id=user_id)
    # The help chat is never a paid company's, so the unpaid AI spend cap always applies.
    await ai_cap.refuse_if_capped(redis, user_id=user_id)

    try:
        known = await help_knowledge(country, body.page)
    except httpx.HTTPError:
        logger.warning("The help chat's knowledge isn't available from rounds", exc_info=True)

        return failed(language)

    messages = build_messages(conversation, language, known, body.page)

    return answer(body, messages, language, user_id)


async def failed(language: str) -> AsyncIterator[str]:
    yield sse_event({"error": translate(CHAT_FAILED, language)})


async def answer(
    body: HelpChatRequest, messages: list[BaseMessage], language: str, user_id: str | None
) -> AsyncIterator[str]:
    """The answer's events: {"delta"}... (and a {"block"} sign-in card), then {"done"} with the
    reply's signature and the answer's id, trace and vote signature, or {"error"}. It counts
    among the instance's streaming turns while it runs."""
    used: dict = {}
    # The answer's id, which a vote on it names, and its Langfuse trace when that's set up.
    answer_id = uuid.uuid4()
    trace_id = new_trace_id()
    chat_id = str(body.chat_id) if body.chat_id else None
    reply = ""
    # Until the answer is written whole, a visitor leaving cut it short.
    outcome = Outcome.CUT
    running["turns"] += 1

    try:
        async for event in with_sign_in(stream_reply(messages, used, trace_id, chat_id)):
            reply += event.get("delta", "")
            yield sse_event(event)

        outcome = Outcome.OK
    except Exception as error:  # noqa: BLE001 - logged by its type only
        outcome = Outcome.FAILED
        # Only the error's type, with its module ("openai.APIConnectionError", which the OpenAI
        # alert counts): its message or traceback could quote the conversation.
        logger.error("Help chat failed: %s.%s", type(error).__module__, type(error).__name__)
        await provider_refused(error, HELP_CHAT, user_id=user_id)
        yield sse_event({"error": translate(CHAT_FAILED, language)})

        return
    finally:
        running["turns"] -= 1

        # However the answer ends, its call is recorded and its tokens count. Shielded, as a
        # visitor leaving cancels the request.
        with anyio.CancelScope(shield=True):
            await record_answer(get_redis(), messages, reply, used.get("usage"), outcome, user_id)

    await track("help_chat_turn", user_id=user_id, turn=len(body.messages))
    key = help_signing_key(settings.service_secret)

    # The page sends the signature back with the reply, which the next answer then reads, and
    # the answer's id, trace and vote signature with a vote on it.
    yield sse_event(
        {
            "done": True,
            "signature": reply_signature(reply, key),
            "answer": {
                "id": str(answer_id),
                "trace_id": trace_id,
                "signature": vote_signature(answer_id, trace_id, key),
            },
        }
    )
