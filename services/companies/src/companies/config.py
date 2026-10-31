from testee_common.config.settings import ServiceSettings


class Settings(ServiceSettings):
    # Cloudflare Turnstile's secret: the "I'm not a robot" check on a job ad's link, a person's
    # first company and an unpaid company's topic review. Empty: no check.
    turnstile_secret_key: str = ""
    # The API description (/docs, /openapi.json) lists every route, internal ones too, so it's
    # served only in development, where the frontend's types are generated from it.
    api_docs: bool = False
    database_url: str
    redis_url: str
    service_secret: str
    generation_url: str
    library_url: str
    rounds_url: str
    billing_url: str
    # Who an account id or an address belongs to, for the admin zone's support tab.
    accounts_url: str
    # Each service holding a kind of integration, for how many are working (the company's menu).
    ats_url: str
    notifications_url: str
    api_url: str
    assistant_url: str
    # Keys the hashes in older invites' credit keys (testee_common.limits.credit_keys, migration 0057).
    person_hash_key: str


settings = Settings()
