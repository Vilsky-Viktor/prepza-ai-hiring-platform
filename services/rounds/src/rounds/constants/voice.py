# Voice mode: an interview's questions read aloud and answered by voice. The candidate's audio
# stays in memory (prepza_common.ai.speech): never written to disk, the database or the logs, and
# neither is what they said.
from enum import StrEnum

# The options' letters, by index, as the interviewer reads them and the candidate says them.
LETTERS = ("A", "B", "C", "D")

# The AI calls voice mode makes, as billing records them.
SPEECH_ACTION = "voice_speech"
TRANSCRIPTION_ACTION = "voice_transcription"
MATCH_ACTION = "voice_match"

# OpenAI's calls: how long each may take and how often it's retried.
MATCH_TIMEOUT_SECONDS = 15
MATCH_RETRIES = 1
MATCH_MAX_TOKENS = 100
SPEECH_TIMEOUT_SECONDS = 30
SPEECH_RETRIES = 1
TRANSCRIBE_TIMEOUT_SECONDS = 20
TRANSCRIBE_RETRIES = 1

# The longest spoken answer the browser sends (it stops listening then).
MAX_ANSWER_SECONDS = 30
# A request's body may be this large on the answer route: a spoken answer, with room for its
# headers (prepza_common.ai.speech.MAX_AUDIO_BYTES).
MAX_ANSWER_BODY_BYTES = 3_000_000
# The most a question's reading adds to its time: a longer clip still plays, but the clock
# starts after this many seconds.
MAX_READING_SECONDS = 90
# Spoken text is cut to this many characters: the rest is on screen.
MAX_SPOKEN_CHARACTERS = 1_500
# Clips nobody has played for this many days are deleted (jobs: voice_clips); a question still
# asked is spoken again then.
CLIP_UNUSED_DAYS = 30
# Clips deleted per batch, each batch its own transaction (they're large: audio).
CLIP_DELETE_BATCH = 100
# The daily clean-up starts no batch after this many seconds; the next run takes the rest.
JOB_SECONDS = 240
# While one request reads a text aloud, it holds the text's lock this long at most (above the
# speech call's timeout and retry), and another request needing the clip checks every
# CLIP_WAIT_SECONDS whether it's done rather than paying for it twice.
CLIP_LOCK_SECONDS = 70
CLIP_WAIT_SECONDS = 0.25
# A clip's last use is written at most this often, so playing it doesn't write every time.
CLIP_TOUCH_HOURS = 24


class Intent(StrEnum):
    """What a spoken answer meant (schemas/voice.py)."""

    CHOOSE = "choose"
    CONFIRM = "confirm"
    REJECT = "reject"
    UNCLEAR = "unclear"


# What the user reads; translated by its English text.
VOICE_FAILED = "Couldn't hear the answer. Please try again or tap an option."
SPEECH_FAILED = "Couldn't read the question aloud."
NOT_VOICE = "This interview isn't taken by voice."
NO_QUESTION = "No question is waiting for an answer."
