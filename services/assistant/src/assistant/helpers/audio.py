from assistant.constants.limits import MAX_AUDIO_SECONDS
from assistant.constants.transcribe import AUDIO_BYTES_PER_SECOND


def audio_seconds(usage, size: int) -> float:
    """A transcribed recording's length: as OpenAI reports it (a "duration" usage), otherwise
    estimated from its size (AUDIO_BYTES_PER_SECOND), at most MAX_AUDIO_SECONDS."""
    seconds = getattr(usage, "seconds", None)

    if seconds:
        return float(seconds)

    return min(size / AUDIO_BYTES_PER_SECOND, MAX_AUDIO_SECONDS)
