from prepza_common.config.settings import ServiceSettings


class Settings(ServiceSettings):
    # The API description lists every route, internal ones too: development only.
    api_docs: bool = False
    # Email settings, accepted terms and recent erasures; Redis holds rate limits and the switches.
    database_url: str
    redis_url: str
    # Signs calls from other services (their users' addresses, settings and accounts).
    service_secret: str
    # Every service holding part of a user's data, for deleting and downloading an account;
    # billing also sets a new account's currency.
    companies_url: str
    rounds_url: str
    generation_url: str
    billing_url: str
    notifications_url: str
    ats_url: str
    api_url: str
    assistant_url: str
    library_url: str


settings = Settings()
