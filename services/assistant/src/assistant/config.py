from prepza_common.config.settings import ServiceSettings
from pydantic import Field


class Settings(ServiceSettings):
    # The API description lists every route, internal ones too: development only.
    api_docs: bool = False
    # Conversations and their messages; Redis counts each user's messages and spending.
    database_url: str
    redis_url: str
    # Signs calls from other services (library deletes and exports a user's conversations).
    service_secret: str
    # OpenAI: the chat and speech-to-text. Empty in CI, where nothing calls OpenAI.
    openai_api_key: str = ""
    # The chat model, and how hard it thinks: "none", "minimal", "low", "medium" or "high".
    assistant_model: str = "gpt-6-luna"
    assistant_reasoning_effort: str = "low"
    # Writes the conversations' titles in the history: a short summary, no reasoning needed.
    title_model: str = "gpt-6-luna"
    title_reasoning_effort: str = "none"
    # Picks the groups of tools a turn is offered (services/tool_routing.py): a few tokens.
    routing_model: str = "gpt-6-luna"
    routing_reasoning_effort: str = "none"
    # Turns a held voice message into text.
    transcribe_model: str = "gpt-4o-mini-transcribe"
    # Conversations nobody has added to for this many days are deleted.
    assistant_retention_days: int = Field(default=90, gt=0)
    # The services whose user-facing GET routes are the assistant's tools, called with the
    # user's own token.
    companies_url: str
    billing_url: str
    library_url: str
    notifications_url: str
    ats_url: str
    api_url: str
    rounds_url: str
    # The site's address: AI apps connect to <SITE_URL>/mcp, and it's the issuer of their access.
    site_url: str
    # Firebase's public web key (the frontend's NEXT_PUBLIC_FIREBASE_API_KEY): an AI app's calls
    # sign the user in with a custom token, to call the other services as them.
    # Required: without it every AI app's call would fail while the service looks healthy.
    firebase_web_api_key: str = Field(min_length=1)


settings = Settings()
