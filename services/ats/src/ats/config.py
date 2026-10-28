from prepza_common.config.settings import ServiceSettings


class Settings(ServiceSettings):
    # The API description lists every route, internal ones too: development only.
    api_docs: bool = False
    # Connections, linked jobs and the candidates an ATS sent; Redis holds maintenance mode.
    database_url: str
    redis_url: str
    # Signs calls from other services (accounts deletes and exports a user's ATS candidates).
    service_secret: str
    # The Fernet key that encrypts companies' ATS keys; empty (or not a key) turns ATS
    # integrations off.
    ats_encryption_key: str = ""
    # The site's public address: where an ATS sends its events, and links in what goes back.
    site_url: str
    # Companies owns companies, members, interviews and invites: who may do what, interview
    # titles, and sending an invite.
    companies_url: str


settings = Settings()
