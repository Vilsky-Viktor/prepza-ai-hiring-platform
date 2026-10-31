"""Voice mode's live listening: a spoken answer heard while the candidate says it. The browser
opens a WebSocket as listening starts, signs in, and once it hears the candidate speaking sends
`start` and the audio (a moment from before the speech included) as it comes; at the end, `end`.
Only the last moment is then left to transcribe. One answer per connection, at most
STREAM_SECONDS. Any refusal or failure closes the connection with a code (STREAM_CLOSE_BASE plus
the HTTP status) and the browser sends the recording to services/voice_answers.py instead, which
gives the candidate the same answer or the same refusal. The audio and the words stay in memory:
never kept or logged."""

import asyncio
import logging
import time
from uuid import UUID

import sentry_sdk
from fastapi import HTTPException, WebSocket, WebSocketDisconnect, status
from openai import OpenAIError
from testee_common.ai import ai_usage
from testee_common.ai.ai_constants import Outcome
from testee_common.auth.auth import verify
from testee_common.auth.user import User

from rounds.config import settings
from rounds.constants.voice import (
    MAX_ANSWER_SECONDS,
    MAX_OPEN_STREAMS,
    MAX_STREAM_FRAME_BYTES,
    STREAM_CLOSE_BASE,
    STREAM_REFUSED,
    STREAM_SECONDS,
    STREAM_SIGN_IN_SECONDS,
    TRANSCRIPTION_ACTION,
)
from rounds.helpers.voice_match import hearing_keywords
from rounds.helpers.voice_pcm import live_resampler, stream_seconds
from rounds.helpers.voice_timing import server_timing
from rounds.integrations.live_hearing import LiveHearing, live_hearing
from rounds.models.sessions import Session
from rounds.schemas.voice import StreamSignIn, StreamStep
from rounds.services import voice_answers, voice_deadline, voice_limits
from rounds.services.session_access import get_own_session
from rounds.services.session_titles import interview_language
from rounds.services.voice_session import shown_question, voice_only

logger = logging.getLogger(__name__)
# This instance's open streams (MAX_OPEN_STREAMS).
stream_slots = asyncio.Semaphore(MAX_OPEN_STREAMS)


class Refused(Exception):
    """The browser sent something out of turn: audio before `start`, a frame too large, more
    than MAX_ANSWER_SECONDS of audio, or an unknown step."""


async def received(websocket: WebSocket) -> bytes | StreamStep:
    """The browser's next message: audio, or a step (ValueError when it's neither)."""
    message = await websocket.receive()

    if message["type"] == "websocket.disconnect":
        raise WebSocketDisconnect(message.get("code", status.WS_1000_NORMAL_CLOSURE))

    if message.get("bytes") is not None:
        return message["bytes"]

    return StreamStep.model_validate_json(message.get("text") or "")


async def signed_in(websocket: WebSocket) -> User:
    """The candidate, from the token in the first message (within STREAM_SIGN_IN_SECONDS),
    checked as a write's is (revoked sign-ins refused); 401 otherwise."""
    async with asyncio.timeout(STREAM_SIGN_IN_SECONDS):
        message = await websocket.receive_text()

    token = StreamSignIn.model_validate_json(message).token
    user = await asyncio.to_thread(verify, token, True)

    if user is None:
        # Only the close code reaches the browser: no message to read.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)

    sentry_sdk.set_user({"id": user.uid})

    return user


async def take_audio(websocket: WebSocket, row: Session, hearing: LiveHearing) -> list[int]:
    """Passes the answer's audio on until its end, counting it as an answer at `start` (over the
    limits, a 429 or 503); gives the choice `waiting` for a yes or no."""
    resample = live_resampler()
    started, size = False, 0

    while True:
        message = await received(websocket)

        if isinstance(message, bytes):
            size += len(message)

            if not started or len(message) > MAX_STREAM_FRAME_BYTES:
                raise Refused

            if stream_seconds(size) > MAX_ANSWER_SECONDS:
                raise Refused

            await hearing.send(resample(message))
        elif message.type == "start" and not started:
            await voice_limits.check_answer(row)
            started = True
        elif message.type == "end" and started:
            await hearing.send(resample(None))

            return sorted(set(message.waiting))
        else:
            raise Refused


async def answer_live(
    websocket: WebSocket, row: Session, user: User, hearing: LiveHearing, language: str
) -> dict[str, float]:
    """One answer: its audio, then, at its end, the question on screen now (it may have changed
    or timed out meanwhile), the arrival noted for the time-up grace as an upload's is
    (services/voice_deadline.py), the final text and its meaning, sent to the browser as
    {"type": "answer", "answer": VoiceAnswerOut, "stages": milliseconds}. Gives the stages'
    seconds."""
    waiting = await take_audio(websocket, row, hearing)
    ended = time.monotonic()
    row = await get_own_session(row.id, user)
    question = shown_question(row)
    await voice_deadline.note_arrival(row, question.question_id)
    said = await hearing.final()
    await record(row, hearing)
    heard_at = time.monotonic()
    understood, by = await voice_answers.understand(row, question, said, waiting, language)
    now = time.monotonic()
    stages = {"transcribe": heard_at - ended, "match": now - heard_at, "total": now - ended}
    voice_answers.log_answer(row, understood, f"{by}, heard live", stages)
    await websocket.send_json(
        {
            "type": "answer",
            "answer": understood.model_dump(mode="json"),
            "stages": {name: round(seconds * 1000) for name, seconds in stages.items()},
        }
    )

    return stages


async def record(row: Session, hearing: LiveHearing) -> None:
    """The audio sent to OpenAI, paid for whether or not it gave the final text: recorded once
    the text is back, or, failed, as the answer ends without it."""
    if not hearing.sent:
        return

    who = voice_answers.who_of(row)
    outcome = Outcome.OK if hearing.done else Outcome.FAILED
    model = settings.transcribe_model
    await ai_usage.record(
        TRANSCRIPTION_ACTION, model, audio_seconds=hearing.seconds, outcome=outcome, **who
    )


async def hear(websocket: WebSocket, session_id: UUID) -> None:
    """The candidate's own voice interview with a question on screen (as the upload's guards),
    then a realtime transcription session told the interview's language and the options' words,
    "ready" once it is, and the answer."""
    user = await signed_in(websocket)
    row = await get_own_session(session_id, user)
    voice_only(row)
    question = shown_question(row)
    await voice_limits.check_stream(row)
    language = await interview_language(row)
    opened = time.monotonic()

    try:
        async with live_hearing(language, hearing_keywords(question)) as hearing:
            await websocket.send_json({"type": "ready"})
            logger.info(
                "Voice stream %s: %s", row.id, server_timing({"open": time.monotonic() - opened})
            )

            try:
                await answer_live(websocket, row, user, hearing, language)
            finally:
                if not hearing.done:
                    await record(row, hearing)
    except OpenAIError as error:
        await ai_usage.provider_refused(error, TRANSCRIPTION_ACTION, row.company_id, row.user_id)
        raise


async def close_code(websocket: WebSocket, session_id: UUID) -> int:
    """Hears one answer; the code to close with: normal, or why it ended without one."""
    if stream_slots.locked():
        return STREAM_CLOSE_BASE + status.HTTP_503_SERVICE_UNAVAILABLE

    try:
        async with stream_slots, asyncio.timeout(STREAM_SECONDS):
            await hear(websocket, session_id)
    except HTTPException as error:
        return STREAM_CLOSE_BASE + error.status_code
    except (Refused, ValueError):
        return STREAM_REFUSED
    except TimeoutError:
        return STREAM_CLOSE_BASE + status.HTTP_504_GATEWAY_TIMEOUT
    except OpenAIError as error:
        logger.warning("Voice mode's live listening failed: %s", type(error).__name__)

        return STREAM_CLOSE_BASE + status.HTTP_502_BAD_GATEWAY

    return status.WS_1000_NORMAL_CLOSURE


async def stream(websocket: WebSocket, session_id: UUID) -> None:
    """A live answer from accepting the connection to closing it; a browser gone meanwhile ends
    it quietly."""
    await websocket.accept()

    try:
        code = await close_code(websocket, session_id)
        await websocket.close(code)
    except (WebSocketDisconnect, RuntimeError):
        return
