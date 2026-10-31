# Voice messages: held, recorded in the browser, turned into text and sent as a message. The
# audio stays in memory: never written to disk, the database or the logs. The formats taken and
# their checks: testee_common.ai.speech.

# A request's body may be this large here: a voice message, with room for its headers.
MAX_BODY_BYTES = 3_000_000
# OpenAI's call: how long it may take and how often it's retried.
TRANSCRIBE_TIMEOUT_SECONDS = 30
TRANSCRIBE_RETRIES = 1

# What the user reads; translated by its English text.
TRANSCRIBE_FAILED = "Couldn't turn the recording into text. Please try again."
