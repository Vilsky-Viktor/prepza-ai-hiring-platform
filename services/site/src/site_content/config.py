from prepza_common.config.settings import ServiceSettings


class Settings(ServiceSettings):
    # The API description lists every route, internal ones too: development only.
    api_docs: bool = False
    # News posts and events waiting to be published; Redis holds rate limits and the switches.
    database_url: str
    redis_url: str
    # Signs calls from other services.
    service_secret: str


settings = Settings()
