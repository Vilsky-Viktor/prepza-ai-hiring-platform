from fastapi import HTTPException, status
from prepza_common.i18n.i18n import translate

from rounds.constants.rounds import RoundStatus
from rounds.constants.voice import NO_QUESTION, NOT_VOICE
from rounds.helpers.sessions import next_session_question
from rounds.helpers.voice_speech import confirmation, question_script
from rounds.models.sessions import Session
from rounds.models.voice_clips import VoiceClip
from rounds.schemas.rounds import NextQuestion
from rounds.services.session_titles import interview_language
from rounds.services.voice_clips import clip_for, made_ahead


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


async def prepare_next(row: Session) -> None:
    """Voice mode, while a question is on the clock: the section's next question read aloud
    ahead, so the step that opens it finds its clip kept. Only the clip cache gets it: nothing of
    that question reaches the candidate before it opens. Nothing after the section's last."""
    shown_question(row)
    following = next_session_question(row, after=1)

    if row.status != RoundStatus.IN_PROGRESS or following is None:
        return

    language = await interview_language(row)
    await made_ahead(row, question_script(following, language), language, company_text=True)


async def phrase_clip(row: Session, phrase: str) -> VoiceClip:
    """One of the interviewer's fixed phrases (constants/voice_phrases.py), in the interview's
    language."""
    language = await interview_language(row)

    return await clip_for(row, translate(phrase, language), language, company_text=False)


async def confirmation_clip(row: Session, picks: list[int]) -> VoiceClip:
    """The interviewer naming the options `picks` and asking whether that's the answer."""
    language = await interview_language(row)

    return await clip_for(row, confirmation(picks, language), language, company_text=False)
