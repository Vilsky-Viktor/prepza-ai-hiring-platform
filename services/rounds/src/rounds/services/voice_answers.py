import logging
import time

from fastapi import HTTPException, Request, status
from openai import OpenAIError
from prepza_common.ai import ai_usage
from prepza_common.ai.ai_constants import Outcome
from prepza_common.ai.llm import estimated_tokens
from prepza_common.ai.speech import audio_seconds, received_audio, speech_to_text

from rounds.config import settings
from rounds.constants.voice import (
    MATCH_ACTION,
    MAX_ANSWER_SECONDS,
    TRANSCRIPTION_ACTION,
    VOICE_FAILED,
    Intent,
)
from rounds.helpers.voice_match import hearing_keywords
from rounds.helpers.voice_timing import server_timing
from rounds.integrations.llm import get_transcribe_client
from rounds.models.sessions import Session
from rounds.schemas.rounds import NextQuestion
from rounds.schemas.voice import VoiceAnswerOut
from rounds.services import voice_deadline, voice_limits, voice_match
from rounds.services.session_titles import interview_language
from rounds.services.voice_session import shown_question, voice_only

logger = logging.getLogger(__name__)


async def failed(error: Exception, action: str, model: str, who: dict, **usage) -> HTTPException:
    """Records a failed call (its type only: the message may quote the candidate) and gives the
    502 the candidate sees; they say it again or tap."""
    logger.warning("Voice mode's %s failed: %s", action, type(error).__name__)
    await ai_usage.provider_refused(error, action, who["company_id"], who["user_id"])
    await ai_usage.record(action, model, outcome=Outcome.FAILED, **who, **usage)

    return HTTPException(status.HTTP_502_BAD_GATEWAY, VOICE_FAILED)


async def hear(request: Request, language: str, who: dict, keywords: list[str]) -> str:
    """The spoken answer as text, in the interview's language, told the words it's likely to
    hear (helpers/voice_match.py hearing_keywords); its cost recorded."""
    content_type, file_name, audio = await received_audio(request)
    model = settings.transcribe_model

    try:
        result = await speech_to_text(
            get_transcribe_client(), model, file_name, audio, content_type, language, keywords
        )
    except OpenAIError as error:
        seconds = audio_seconds(None, len(audio), MAX_ANSWER_SECONDS)
        raise await failed(error, TRANSCRIPTION_ACTION, model, who, audio_seconds=seconds)

    seconds = audio_seconds(getattr(result, "usage", None), len(audio), MAX_ANSWER_SECONDS)
    await ai_usage.record(TRANSCRIPTION_ACTION, model, audio_seconds=seconds, **who)

    return result.text.strip()


def who_of(row: Session) -> dict:
    """Whose AI use an answer is, as billing records it."""
    return {"company_id": row.company_id, "user_id": row.user_id, "subject_id": row.id}


async def understand(
    row: Session, question: NextQuestion, said: str, waiting: list[int], language: str
) -> tuple[VoiceAnswerOut, str]:
    """What was said, matched to the question's options (or to a yes or no for the choice
    `waiting`), the matching call's cost recorded; with "model" or "code", whichever read it. A
    failed call is a 502."""
    model = settings.voice_match_model
    who = who_of(row)

    try:
        intent, picks, usage = await voice_match.match(
            question, said, waiting, language, str(row.id)
        )
    except Exception as error:  # noqa: BLE001 - recorded and logged by its type only
        usage = {"input_tokens": estimated_tokens(said + question.text)}
        raise await failed(error, MATCH_ACTION, model, who, usage=usage)

    # Noise, a plain yes or only letters were read without a call: nothing to record.
    if usage is not None:
        await ai_usage.record(MATCH_ACTION, model, usage, **who)

    clear = intent == Intent.CHOOSE and not question.multi
    understood = VoiceAnswerOut(heard=said, intent=intent, picks=picks, clear=clear)

    return understood, "model" if usage is not None else "code"


def log_answer(row: Session, understood: VoiceAnswerOut, by: str, stages: dict[str, float]):
    """One line per answer: the session's id, the intent, what read it and the stages' times;
    never the words."""
    logger.info(
        "Voice answer %s: %s by %s, %s", row.id, understood.intent, by, server_timing(stages)
    )


async def answer(
    row: Session, request: Request, waiting: list[int]
) -> tuple[VoiceAnswerOut, dict[str, float]]:
    """A spoken answer to the question on screen, recorded whole and uploaded (when it couldn't be
    heard live, services/voice_stream.py), understood: heard, then matched to its options (or to
    a yes or no for the choice `waiting` for confirmation); a sound without words is noise, which
    the browser ignores. Nothing is saved here: a clear choice (one option on a single-answer
    question) is sent at once, any other once the candidate confirms it, as a tapped one is. With
    it, each stage's seconds (transcribe, match, total), also logged with the session's id and
    the intent: never the words. The audio and the words are never kept or logged. Over the
    limits a 429 (or 503); a failed call a 502."""
    started = time.monotonic()
    voice_only(row)
    question = shown_question(row)
    # Noted as it arrives, before the upload is read: in time, its answer may come after the
    # deadline (services/voice_deadline.py).
    await voice_deadline.note_arrival(row, question.question_id)
    await voice_limits.check_answer(row)
    language = await interview_language(row)
    heard_at = time.monotonic()
    said = await hear(request, language, who_of(row), hearing_keywords(question))
    matched_at = time.monotonic()
    understood, by = await understand(row, question, said, waiting, language)
    now = time.monotonic()
    stages = {
        "transcribe": matched_at - heard_at,
        "match": now - matched_at,
        "total": now - started,
    }
    log_answer(row, understood, by, stages)

    return understood, stages
