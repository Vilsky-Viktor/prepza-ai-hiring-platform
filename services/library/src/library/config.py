from prepza_common.config.settings import ServiceSettings


class Settings(ServiceSettings):
    # The API description (/docs, /openapi.json) lists every route, internal ones too, so it's
    # served only in development, where the frontend's types are generated from it.
    api_docs: bool = False
    database_url: str
    redis_url: str
    service_secret: str
    rounds_url: str
    generation_url: str
    companies_url: str
    billing_url: str
    notifications_url: str
    ats_url: str
    api_url: str
    assistant_url: str
    # Users' email settings and accepted terms; its old routes here forward to it.
    accounts_url: str


settings = Settings()
