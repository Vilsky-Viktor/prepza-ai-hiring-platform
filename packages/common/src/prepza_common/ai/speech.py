"""Speech recorded in a browser and turned into text by OpenAI (the assistant's voice messages, a
candidate's spoken answers): the formats taken, their checks, their length and the call. The
audio stays in memory: never written to disk, a database or the logs."""

from fastapi import HTTPException, Request, status

# The largest recording (a minute of compressed speech is well under it).
MAX_AUDIO_BYTES = 2 * 1024 * 1024
# The formats browsers record in, and the file name OpenAI reads the format from.
AUDIO_FILES = {
    "audio/webm": "audio.webm",
    "audio/mp4": "audio.mp4",
    "audio/ogg": "audio.ogg",
}
# How each format's file starts (its container's magic bytes), checked before OpenAI reads it: a
# body that isn't the recording its Content-Type claims is refused (415). (offset, bytes)
AUDIO_SIGNATURES = {
    "audio/webm": (0, b"\x1a\x45\xdf\xa3"),
    "audio/mp4": (4, b"ftyp"),
    "audio/ogg": (0, b"OggS"),
}
# The interface's language codes OpenAI knows by another code.
TRANSCRIBE_LANGUAGES = {"fil": "tl"}
# A recording's length when OpenAI doesn't report it: its size over this rate (32 kbit/s, speech
# in Opus as browsers record it). Higher bitrates read as longer, so its cost is overestimated
# rather than missed.
AUDIO_BYTES_PER_SECOND = 4_000

# What the user reads; translated by its English text.
AUDIO_TOO_LARGE = "The recording is too long."
AUDIO_NOT_SUPPORTED = "This recording format isn't supported."
NOTHING_HEARD = "Couldn't hear anything. Try again."


async def read_audio(request: Request) -> bytes:
    """The recording in the request's body, in memory; over MAX_AUDIO_BYTES, a 413 before more
    of it is read."""
    if int(request.headers.get("content-length") or 0) > MAX_AUDIO_BYTES:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, AUDIO_TOO_LARGE)

    audio = bytearray()

    async for chunk in request.stream():
        audio += chunk

        if len(audio) > MAX_AUDIO_BYTES:
            raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, AUDIO_TOO_LARGE)

    return bytes(audio)


def recording_format(request: Request) -> tuple[str, str]:
    """The recording's media type and the file name OpenAI reads it by; another format is a
    415, before the body is read."""
    content_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
    file_name = AUDIO_FILES.get(content_type)

    if file_name is None:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, AUDIO_NOT_SUPPORTED)

    return content_type, file_name


async def received_audio(request: Request) -> tuple[str, str, bytes]:
    """The request's recording, checked: its media type, the file name OpenAI reads it by and its
    bytes. Another format, or a body that doesn't start as that format does, is a 415; a larger
    one a 413; an empty one a 422."""
    content_type, file_name = recording_format(request)
    audio = await read_audio(request)

    if not audio:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, NOTHING_HEARD)

    offset, signature = AUDIO_SIGNATURES[content_type]

    if audio[offset : offset + len(signature)] != signature:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, AUDIO_NOT_SUPPORTED)

    return content_type, file_name, audio


def audio_seconds(usage, size: int, max_seconds: float) -> float:
    """A transcribed recording's length: as OpenAI reports it (a "duration" usage), otherwise
    estimated from its size (AUDIO_BYTES_PER_SECOND), at most `max_seconds`."""
    seconds = getattr(usage, "seconds", None)

    if seconds:
        return float(seconds)

    return min(size / AUDIO_BYTES_PER_SECOND, max_seconds)


async def speech_to_text(
    client,
    model: str,
    file_name: str,
    audio: bytes,
    content_type: str,
    language: str,
    keywords: list[str] | None = None,
):
    """OpenAI's transcription of a recording (`client` is an AsyncOpenAI), told its language and,
    when given, words it's likely to hear (`keywords`)."""
    hints = {"keywords": keywords} if keywords else {}

    return await client.audio.transcriptions.create(
        model=model,
        file=(file_name, audio, content_type),
        languages=[TRANSCRIBE_LANGUAGES.get(language, language)],
        **hints,
    )
