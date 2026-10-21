from prepza_common.settings import ServiceSettings


class Settings(ServiceSettings):
    # The API description lists every route, internal ones too: development only.
    api_docs: bool = False
    database_url: str
    # The limits' values every service reads and the unpaid AI spend cap's counter.
    redis_url: str
    service_secret: str
    # The services asked for names in the AI costs tab: companies' names, accounts' emails.
    companies_url: str
    library_url: str
    # Paddle: "sandbox" or "production", the client-side token for Paddle.js (public by design),
    # and the secret that signs its webhooks.
    paddle_environment: str = "sandbox"
    paddle_client_token: str = ""
    paddle_webhook_secret: str = ""
    # The Paddle product every top-up is sold under, at the price billing works out in the
    # buyer's currency (helpers/credits.py); without it, nothing is sold.
    paddle_product_candidates: str = ""
    # Automatic top-up: the server-side API key that charges the saved card, and the $0
    # monthly price whose checkout saves it. Without both, it isn't offered.
    paddle_api_key: str = ""
    paddle_price_auto_top_up: str = ""


settings = Settings()
