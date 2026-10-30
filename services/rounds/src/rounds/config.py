from prepza_common.config.settings import ServiceSettings


class Settings(ServiceSettings):
    # The API description (/docs, /openapi.json) lists every route, internal ones too, so it's
    # served only in development, where the frontend's types are generated from it.
    api_docs: bool = False
    database_url: str
    redis_url: str
    library_url: str
    service_secret: str
    # OpenAI: voice mode's speech, its hearing and its matching. Empty in CI, where nothing calls
    # OpenAI.
    openai_api_key: str = ""
    # Turns what a candidate said into the options they meant (services/voice_match.py).
    voice_match_model: str = "gpt-6-luna"
    voice_match_reasoning_effort: str = "none"
    # Reads questions and the interviewer's phrases aloud, once each (cached in voice_clips): a
    # realtime voice model told to say the text exactly (OpenAI's text-to-speech models shut down).
    speech_model: str = "gpt-realtime-2.1-mini"
    speech_voice: str = "marin"
    # Turns a candidate's spoken answer into text: streamed to it while they speak and transcribed
    # as they stop (services/voice_stream.py), or a whole recording when streaming isn't possible
    # (services/voice_answers.py). gpt-live-transcribe, which transcribes as it hears, was as fast
    # at the end and heard worse (evals/baselines/voice-mode.md, 2026-10-31).
    transcribe_model: str = "gpt-transcribe"


settings = Settings()
