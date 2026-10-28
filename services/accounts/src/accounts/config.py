from prepza_common.config.settings import ServiceSettings


class Settings(ServiceSettings):
    # The API description lists every route, internal ones too: development only.
    api_docs: bool = False
    # Email settings, accepted terms and recent erasures; Redis holds rate limits and the switches.
    database_url: str
    redis_url: str
    # Signs calls from other services (their users' addresses, settings and accounts).
    service_secret: str
    # A new account's currency, from the country it signed up in.
    billing_url: str


settings = Settings()
