import asyncio
import logging
from collections.abc import AsyncIterator

import anyio
from fastapi import HTTPException, status
from prepza_common.ai.secrets_check import secret_in
from prepza_common.auth.user import User
from prepza_common.config.constants import RETRY_AFTER
from prepza_common.http.sse import KEEP_ALIVE, sse_event
from prepza_common.i18n.i18n import translate
from prepza_common.limits.pause import refuse_if_paused

from assistant.constants.ai_usage import MESSAGE_ACTION
from assistant.constants.chat import (
    CHAT_FAILED,
    HISTORY_CHARACTERS,
    HISTORY_MESSAGES,
    KEEP_ALIVE_SECONDS,
    SESSION_EXPIRED,
    SESSION_EXPIRED_CODE,
    TITLE_LENGTH,
    TURN_SECONDS,
    TURNS_AT_ONCE,
    TURNS_BUSY_RETRY_SECONDS,
    Status,
)
from assistant.core.db import Session
from assistant.integrations.redis import get_redis
from assistant.models.answers import Answer, Turn
from assistant.repositories import actions as pending_actions
from assistant.repositories import conversations, messages
from assistant.schemas.chat import ChatRequest
from assistant.services import limits, show, titles
from assistant.services.chat import Emit, SessionExpired, build_messages, converse
from assistant.services.conversations import open_conversation
from assistant.services.secrets import secret_reply
from assistant.services.tenancy import require_company, user_companies

logger = logging.getLogger(__name__)

# What the turn puts last on its queue: nothing more comes.
END = object()
# Turns streaming on this instance now (stream); at most TURNS_AT_ONCE.
running = {"turns": 0}


def refuse_if_busy() -> None:
    """Refuses a new turn (503, with Retry-After) while this instance streams TURNS_AT_ONCE; the
    panel shows the error to try again."""
    if running["turns"] >= TURNS_AT_ONCE:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            CHAT_FAILED,
            headers={RETRY_AFTER: str(TURNS_BUSY_RETRY_SECONDS)},
        )


async def start(body: ChatRequest, user: User, token: str, language: str) -> AsyncIterator[str]:
    """Checks a new message before anything streams (plain HTTP errors): the pause, the
    conversation (the user's own, about a company they can still see), the limits. Then saves it
    and returns the turn's events. A message with a secret in it (or in the chat sent along) is
    answered before anything else, and nothing of it is kept."""
    secret = secret_in([body.message, *(turn.content for turn in body.earlier)])

    if secret is not None:
        return secret_reply(secret, body, language)

    refuse_if_busy()
    redis = get_redis()
    await refuse_if_paused(redis, MESSAGE_ACTION, user_id=user.uid)
    conversation = None
    company_id = body.company_id

    if body.conversation_id is not None:
        conversation = await open_conversation(body.conversation_id, user.uid, token, language)

    # The company picked in the panel, for this message: one of the user's, or none.
    companies = await user_companies(user.uid)
    require_company(company_id, companies)

    await limits.check(redis, user.uid, company_id)
    page = body.page.model_dump(exclude_none=True) if body.page else None

    # A new conversation, the chat from before signing in and the question: one save.
    async with Session.begin() as session:
        if conversation is None:
            title = body.message[:TITLE_LENGTH]
            conversation = await conversations.create(session, user.uid, company_id, title)

            if body.earlier:
                await messages.add_earlier(session, conversation.id, body.earlier)

        earlier = await messages.recent(session, conversation.id, HISTORY_MESSAGES)
        await messages.add_question(session, conversation.id, body.message, body.source, page)

    turn = Turn(conversation.id, user.uid, company_id, token, language, companies, user.name)

    return stream(turn, build_messages(turn, earlier, body.message, page, HISTORY_CHARACTERS))


async def stream(turn: Turn, prompt: list, first: dict | None = None) -> AsyncIterator[str]:
    """The turn's events: the conversation's id first (and `first`, when given), a keep-alive comment whenever nothing
    came for KEEP_ALIVE_SECONDS. The turn runs as a task of its own; when the client goes (the
    user stopped it, or closed the tab), it's cancelled and saves what it had."""
    queue: asyncio.Queue = asyncio.Queue()
    task = asyncio.create_task(run_turn(turn, prompt, queue.put_nowait))
    running["turns"] += 1

    try:
        yield sse_event({"conversation": {"id": str(turn.conversation_id)}})

        if first is not None:
            yield sse_event(first)

        while True:
            try:
                event = await asyncio.wait_for(queue.get(), KEEP_ALIVE_SECONDS)
            except TimeoutError:
                yield KEEP_ALIVE

                continue

            if event is END:
                return

            yield sse_event(event)
    finally:
        task.cancel()

        # The request may be cancelled itself: waiting for the turn to save must not be.
        with anyio.CancelScope(shield=True):
            await asyncio.wait({task})

        running["turns"] -= 1


async def run_turn(turn: Turn, prompt: list, emit: Emit) -> None:
    """Runs the conversation loop within TURN_SECONDS and saves the answer however it ends:
    complete, cancelled (with its text so far) or failed. Its tokens count against the budgets.
    Ends with {"done": {"message_id"}} or a translated {"error"}, then END."""
    answer = Answer()
    status = Status.COMPLETE
    error = None

    try:
        async with asyncio.timeout(TURN_SECONDS):
            await converse(prompt, turn, answer, emit)
            await show.finish(answer, turn, emit)
    except asyncio.CancelledError:
        # Nobody reads the events any more; the answer is still saved below.
        asyncio.current_task().uncancel()
        status = Status.CANCELLED
    except SessionExpired:
        status = Status.FAILED
        error = {"error": translate(SESSION_EXPIRED, turn.language), "code": SESSION_EXPIRED_CODE}
    except Exception as failure:  # noqa: BLE001 - logged by its type only
        # The model failed, or the turn ran out of time. Only the error's type, with its module
        # ("openai.APIConnectionError", which the OpenAI alert counts): its message or traceback
        # could quote the conversation.
        logger.error(
            "An assistant turn failed: %s.%s", type(failure).__module__, type(failure).__name__
        )
        status = Status.FAILED
        error = {"error": translate(CHAT_FAILED, turn.language)}

    await limits.record(get_redis(), turn.user_id, turn.company_id, answer.tokens)
    last = error or {"error": translate(CHAT_FAILED, turn.language)}

    try:
        async with Session.begin() as session:
            message_id = await messages.add_answer(session, turn.conversation_id, answer, status)

        # Its cards show under it again when the conversation is opened, while they wait.
        for action_id in answer.pending:
            await pending_actions.attach(action_id, message_id)

        if error is None:
            last = {"done": {"message_id": str(message_id)}}
    except Exception as failure:  # noqa: BLE001 - logged by its type only
        # The conversation was deleted meanwhile (its company, or by the user).
        logger.error("Couldn't save an assistant answer: %s", type(failure).__name__)
    finally:
        # However the turn ended, the panel hears how, and the stream ends; after a new
        # question's answer, with the conversation's new title when it's time for one.
        emit(last)

        if turn.new_question and "done" in last:
            title = await titles.refresh(turn)

            if title:
                emit({"title": title})

        emit(END)
