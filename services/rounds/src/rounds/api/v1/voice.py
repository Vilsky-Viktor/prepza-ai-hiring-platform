from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, Query, Request, Response, WebSocket, status
from pydantic import Field
from testee_common.auth.auth import CurrentUser

from rounds.constants.rounds import OPTIONS_PER_QUESTION
from rounds.constants.voice_phrases import FIXED_PHRASES, Phrase
from rounds.helpers.voice_timing import server_timing
from rounds.schemas.voice import VoiceAnswerOut
from rounds.services import voice_answers, voice_session, voice_stream
from rounds.services.session_access import get_own_session

router = APIRouter(prefix="/sessions", tags=["voice"])

Option = Annotated[int, Field(ge=0, lt=OPTIONS_PER_QUESTION)]
Picks = Annotated[list[Option] | None, Query(max_length=OPTIONS_PER_QUESTION)]
Chosen = Annotated[list[Option], Query(min_length=1, max_length=OPTIONS_PER_QUESTION)]
OGG = "audio/ogg"


@router.get("/{session_id}/voice/question", response_class=Response)
async def question_audio(session_id: UUID, user: CurrentUser) -> Response:
    """Voice mode: the question on screen and its options read aloud (Ogg Opus), once its clock
    started (its reading counts in its time). Made on the first request, or ahead while the
    question before it was on screen, and kept for every candidate who gets it."""
    row = await get_own_session(session_id, user)
    voice_session.voice_only(row)
    clip = await voice_session.question_clip(row, voice_session.shown_question(row))

    return Response(clip.audio, media_type=OGG)


@router.post(
    "/{session_id}/voice/next-question/prepare",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def prepare_next_question(session_id: UUID, user: CurrentUser) -> Response:
    """Voice mode, as a question opens: the next question of the section read aloud ahead and
    kept, so moving on doesn't wait for it. Nothing of it is sent: it's heard only once it
    opens. Counted against the voice limits when it's new."""
    row = await get_own_session(session_id, user)
    voice_session.voice_only(row)
    await voice_session.prepare_next(row)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{session_id}/voice/phrases/{phrase}", response_class=Response)
async def phrase_audio(session_id: UUID, phrase: Phrase, user: CurrentUser) -> Response:
    """Voice mode: one of the interviewer's phrases read aloud (Ogg Opus) in the interview's
    language."""
    row = await get_own_session(session_id, user)
    voice_session.voice_only(row)
    clip = await voice_session.phrase_clip(row, FIXED_PHRASES[phrase])

    return Response(clip.audio, media_type=OGG)


@router.get("/{session_id}/voice/confirmations", response_class=Response)
async def confirmation_audio(session_id: UUID, picks: Chosen, user: CurrentUser) -> Response:
    """Voice mode: the interviewer naming the options in `picks` (indices) and asking whether
    that's the candidate's answer, read aloud (Ogg Opus)."""
    row = await get_own_session(session_id, user)
    voice_session.voice_only(row)
    clip = await voice_session.confirmation_clip(row, sorted(set(picks)))

    return Response(clip.audio, media_type=OGG)


@router.get("/{session_id}/voice/saved/{pick}", response_class=Response)
async def saved_audio(
    session_id: UUID, pick: Annotated[int, Path(ge=0, lt=OPTIONS_PER_QUESTION)], user: CurrentUser
) -> Response:
    """Voice mode: the interviewer saying a clear answer's option (`pick`, its index) was saved,
    read aloud (Ogg Opus)."""
    row = await get_own_session(session_id, user)
    voice_session.voice_only(row)
    clip = await voice_session.saved_clip(row, pick)

    return Response(clip.audio, media_type=OGG)


@router.post("/{session_id}/voice/answers")
async def voice_answer(
    session_id: UUID, request: Request, response: Response, user: CurrentUser, waiting: Picks = None
) -> VoiceAnswerOut:
    """Voice mode: a spoken answer to the question on screen, understood. The body is the
    recording (audio/webm, audio/mp4 or audio/ogg, at most 2 MB); `waiting` is the choice (option
    indices) waiting for the candidate's yes or no. Nothing is saved: a clear choice, or a
    confirmed one, is sent to the answers route as a tapped one is. The audio and the words are
    never kept. The `Server-Timing` header gives the stages' milliseconds: transcribe, match,
    total."""
    row = await get_own_session(session_id, user)
    understood, stages = await voice_answers.answer(row, request, sorted(set(waiting or [])))
    response.headers["Server-Timing"] = server_timing(stages)

    return understood


@router.websocket("/{session_id}/voice/stream")
async def voice_stream_answer(websocket: WebSocket, session_id: UUID) -> None:
    """Voice mode: a spoken answer heard live, while the candidate says it (services/
    voice_stream.py has the messages). Signed in by the first message, not a header (a browser
    can't set one on a WebSocket), and guarded as the answers route is: the candidate's own voice
    interview, a question on screen, the voice limits. One answer per connection, closed with
    4000 plus the answers route's status when refused; the browser then uploads the recording."""
    await voice_stream.stream(websocket, session_id)
