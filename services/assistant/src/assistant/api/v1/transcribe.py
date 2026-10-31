from fastapi import APIRouter, Request
from testee_common.i18n.i18n import request_language

from assistant.api.dependencies import UserWithToken
from assistant.schemas.transcribe import TranscriptOut
from assistant.services import transcribe as transcription

router = APIRouter(tags=["chat"])


@router.post("/transcribe")
async def transcribe(request: Request, auth: UserWithToken) -> TranscriptOut:
    """A held voice message as text, which the panel then sends as a message. The body is the
    recording itself (Content-Type audio/webm, audio/mp4 or audio/ogg, at most 2 MB), heard in
    the interface's language. Never stored or logged."""
    user, _ = auth
    text = await transcription.transcribe(request, user.uid, request_language(request))

    return TranscriptOut(text=text)
