from testee_common.config.settings import ServiceSettings


class Settings(ServiceSettings):
    # The API description lists every route, internal ones too: development only.
    api_docs: bool = False
    # Email settings, accepted terms and recent erasures; Redis holds rate limits and the switches.
    database_url: str
    redis_url: str
    # Signs calls from other services (their users' addresses, settings and accounts).
    service_secret: str
    # Every service holding part of a user's data, for downloading an account (deleting one is
    # companies' call, then the user.deleted event); billing also sets a new account's currency.
    companies_url: str
    rounds_url: str
    generation_url: str
    billing_url: str
    notifications_url: str
    ats_url: str
    api_url: str
    assistant_url: str
    library_url: str
    # The site's content service (contact messages); SITE_URL is the site's own address.
    site_service_url: str


settings = Settings()
