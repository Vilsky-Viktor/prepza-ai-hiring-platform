from prepza_common.config.settings import ServiceSettings


class Settings(ServiceSettings):
    # Companies' API keys and web hooks; Redis holds the rate limits and maintenance mode.
    database_url: str
    redis_url: str
    # Signs calls from other services (library deletes and exports a user's keys).
    service_secret: str
    # The Fernet key that encrypts web hooks' signing secrets; empty (or not a key), web hooks
    # can't be added and none is sent.
    api_encryption_key: str = ""
    # The site's public address: links to candidates' results in what the API returns.
    site_url: str
    # Companies owns companies, members, interviews and invites: who may do what, and the
    # interviews and candidates the API returns.
    companies_url: str


settings = Settings()
