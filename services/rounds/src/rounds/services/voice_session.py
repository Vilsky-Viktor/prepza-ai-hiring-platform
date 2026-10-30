import logging
import math

from fastapi import HTTPException, status
from prepza_common.i18n.i18n import translate

from rounds.constants.voice import MAX_READING_SECONDS, NO_QUESTION, NOT_VOICE
from rounds.helpers.sessions import next_session_question
from rounds.helpers.voice_speech import confirmation, question_script
from rounds.models.sessions import Session
from rounds.models.voice_clips import VoiceClip
from rounds.schemas.rounds import NextQuestion
from rounds.services.session_titles import interview_language
from rounds.services.voice_clips import clip_for

logger = logging.getLogger(__name__)


def voice_only(row: Session) -> None:
    """Voice mode's routes answer only a voice interview (409 otherwise)."""
    if not row.voice:
        raise HTTPException(status.HTTP_409_CONFLICT, NOT_VOICE)


def shown_question(row: Session) -> NextQuestion:
    """The question waiting for an answer, once its clock started: a question is never heard
    before it's on the clock (409 otherwise)."""
    question = next_session_question(row) if row.question_shown_at else None

    if question is None:
        raise HTTPException(status.HTTP_409_CONFLICT, NO_QUESTION)

    return question


async def question_clip(row: Session, question: NextQuestion) -> VoiceClip:
    """The question and its options, read aloud in the interview's language."""
    language = await interview_language(row)

    return await clip_for(row, question_script(question, language), language, company_text=True)


async def phrase_clip(row: Session, phrase: str) -> VoiceClip:
    """One of the interviewer's fixed phrases (constants/voice_phrases.py), in the interview's
    language."""
    language = await interview_language(row)

    return await clip_for(row, translate(phrase, language), language, company_text=False)


async def confirmation_clip(row: Session, picks: list[int]) -> VoiceClip:
    """The interviewer naming the options `picks` and asking whether that's the answer."""
    language = await interview_language(row)

    return await clip_for(row, confirmation(picks, language), language, company_text=False)


async def reading_seconds(row: Session) -> int | None:
    """Voice mode, before a question's clock starts: the seconds its reading aloud adds (at most
    MAX_READING_SECONDS), its clip made now when it's new. None when the question isn't read
    (click mode, already on the clock) or reading it failed: it then goes on unread."""
    question = next_session_question(row)

    if not row.voice or row.question_shown_at is not None or question is None:
        return None

    try:
        clip = await question_clip(row, question)
    except HTTPException as error:
        logger.warning("Question %s goes on unread: %s", question.question_id, error.status_code)

        return None

    return min(math.ceil(clip.seconds), MAX_READING_SECONDS)
