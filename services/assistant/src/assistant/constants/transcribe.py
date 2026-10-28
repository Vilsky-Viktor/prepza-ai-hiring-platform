# Voice messages: held, recorded in the browser, turned into text and sent as a message. The
# audio stays in memory: never written to disk, the database or the logs.

# The largest recording (a minute of compressed speech is well under it).
MAX_AUDIO_BYTES = 2 * 1024 * 1024
# A request's body may be this large here: a voice message, with room for its headers.
MAX_BODY_BYTES = 3_000_000
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
# OpenAI's call: how long it may take and how often it's retried.
TRANSCRIBE_TIMEOUT_SECONDS = 30
TRANSCRIBE_RETRIES = 1

# What the user reads; translated by its English text.
AUDIO_TOO_LARGE = "The recording is too long."
AUDIO_NOT_SUPPORTED = "This recording format isn't supported."
NOTHING_HEARD = "Couldn't hear anything. Try again."
TRANSCRIBE_FAILED = "Couldn't turn the recording into text. Please try again."
# A recording's length when OpenAI doesn't report it: its size over this rate (32 kbit/s, speech
# in Opus as browsers record it), at most MAX_AUDIO_SECONDS. Higher bitrates read as longer, so
# its cost is overestimated rather than missed.
AUDIO_BYTES_PER_SECOND = 4_000
