from prepza_common.config.settings import ServiceSettings


class Settings(ServiceSettings):
    # Cloudflare Turnstile's secret: the "I'm not a robot" check on the contact form. Empty: no
    # check.
    turnstile_secret_key: str = ""
    # The API description lists every route, internal ones too: development only.
    api_docs: bool = False
    # News posts and events waiting to be published; Redis holds rate limits, the limits the
    # platform guide names, and the switches.
    database_url: str
    redis_url: str
    # Signs calls from other services.
    service_secret: str
    # Billing's public prices, which the FAQ and the platform guide name.
    billing_url: str


settings = Settings()
