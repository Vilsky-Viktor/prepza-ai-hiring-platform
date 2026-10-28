from prepza_common.config.settings import ServiceSettings


class Settings(ServiceSettings):
    # Cloudflare Turnstile's secret: the "I'm not a robot" check on the contact form. Empty: no
    # check.
    turnstile_secret_key: str = ""
    # The API description (/docs, /openapi.json) lists every route, internal ones too, so it's
    # served only in development, where the frontend's types are generated from it.
    api_docs: bool = False
    database_url: str
    redis_url: str
    library_url: str
    # The site's content service (SITE_URL is the site's own address): rounds' old content routes
    # forward there for one release.
    site_service_url: str
    service_secret: str


settings = Settings()
