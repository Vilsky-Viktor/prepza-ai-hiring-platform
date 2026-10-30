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
# A reading is made at most this many times: again when it fails or strays from its text.
SPEECH_ATTEMPTS = 2
# The speech model's audio: 16-bit mono PCM at this rate, kept as Ogg Opus at this bit rate.
SPEECH_RATE = 24_000
OPUS_BIT_RATE = 32_000
# A reading strays when the model's own transcript of it has more word errors than this share of
# the text's words, or this many words in a row the text hasn't (an answer, a comment).
MAX_READING_WORD_ERRORS = 0.1
MAX_ADDED_WORDS = 3
TRANSCRIBE_TIMEOUT_SECONDS = 20
TRANSCRIBE_RETRIES = 1

# Live listening (services/voice_stream.py): a spoken answer streamed to rounds over a WebSocket
# while the candidate says it, and on to OpenAI's realtime transcription, so its text is ready
# moments after they stop. The browser sends 16-bit mono PCM at STREAM_RATE (its speech
# detector's frames); OpenAI takes it at LIVE_RATE.
STREAM_RATE = 16_000
LIVE_RATE = 24_000
# A frame larger than this is refused (the detector's are 1,024 bytes).
MAX_STREAM_FRAME_BYTES = 16_384
# The browser opens a stream as listening starts and must sign in within STREAM_SIGN_IN_SECONDS;
# a stream lives at most STREAM_SECONDS (under Cloud Run's 60-second request timeout: the browser
# opens a new one when a quiet one is 25 seconds old) and hears one answer.
STREAM_SIGN_IN_SECONDS = 5
STREAM_SECONDS = 55
# Streams are held while candidates speak, so an instance keeps at most this many open (of its 40
# requests at once, infra/terraform/locals.tf): the rest of its slots stay for short requests,
# and a candidate over it has the recording uploaded instead (a 503 close).
MAX_OPEN_STREAMS = 20
# OpenAI's session: how long opening it and the final transcript after the answer's end may take.
LIVE_OPEN_TIMEOUT_SECONDS = 10
LIVE_FINAL_TIMEOUT_SECONDS = 5
# A stream's close codes beyond a normal close: 4000 plus the HTTP status the upload would get
# (4401 not signed in, 4404 not their session, 4409 not a voice interview or no question, 4429
# over a limit, 4502 OpenAI failed), and STREAM_REFUSED for anything the browser sent wrong. The
# browser sends the recording the usual way after any of them.
STREAM_CLOSE_BASE = 4000
STREAM_REFUSED = 4400

# The longest spoken answer the browser sends (it stops listening then).
MAX_ANSWER_SECONDS = 30
# A spoken answer that reached the service by its question's deadline plus this many seconds (a
# recording sent as the time ran out, still uploading) counts once it's understood, without a
# confirmation, when the answer it gives arrives within VOICE_ANSWER_GRACE_SECONDS of the
# deadline (the browser waits about 10 seconds for it). Noted in Redis under IN_TIME_KEY, with
# the question's id, until that grace ends.
VOICE_UPLOAD_SECONDS = 2
VOICE_ANSWER_GRACE_SECONDS = 15
IN_TIME_KEY = "voice:in-time:{session_id}"
# A request's body may be this large on the answer route: a spoken answer, with room for its
# headers (prepza_common.ai.speech.MAX_AUDIO_BYTES).
MAX_ANSWER_BODY_BYTES = 3_000_000
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
    # No words at all (a cough, a knock, thunder): ignored, as if nothing was said. Decided by code
    # (helpers/voice_match.py is_noise), never by the model.
    NOISE = "noise"


# What the user reads; translated by its English text.
VOICE_FAILED = "Couldn't hear the answer.\nPlease try again or tap an option."
SPEECH_FAILED = "Couldn't read the question aloud."
NOT_VOICE = "This interview isn't taken by voice."
NO_QUESTION = "No question is waiting for an answer."
