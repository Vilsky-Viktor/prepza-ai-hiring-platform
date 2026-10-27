from prepza_common.config.settings import ServiceSettings


class Settings(ServiceSettings):
    # Cloudflare Turnstile's secret: the "I'm not a robot" check on the contact form and a
    # visitor's first help chat message. Empty: no check.
    turnstile_secret_key: str = ""
    # The API description (/docs, /openapi.json) lists every route, internal ones too, so it's
    # served only in development, where the frontend's types are generated from it.
    api_docs: bool = False
    database_url: str
    redis_url: str
    library_url: str
    billing_url: str
    service_secret: str
    # The FAQ's help chat, free for everyone and answering from fixed texts: fast and cheap.
    help_model: str = "gpt-6-luna"
    # How hard it thinks: "none" (which also lets it take a temperature), "minimal", "low",
    # "medium" or "high".
    help_reasoning_effort: str = "none"


settings = Settings()
