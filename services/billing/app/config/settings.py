from typing import Literal

from prepza_common.config.settings import ServiceSettings
from pydantic import model_validator

from app.constants.products import PADDLE_KEY_PREFIXES, PADDLE_TOKEN_PREFIXES


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
    paddle_environment: Literal["sandbox", "production"] = "sandbox"
    paddle_client_token: str = ""
    paddle_webhook_secret: str = ""
    # The Paddle product every top-up is sold under, at the price billing works out in the
    # buyer's currency (helpers/credits.py); without it, nothing is sold.
    paddle_product_candidates: str = ""
    # Automatic top-up: the server-side API key that charges the saved card, and the $0
    # monthly price whose checkout saves it. Without both, it isn't offered.
    paddle_api_key: str = ""
    paddle_price_auto_top_up: str = ""
    # Keys the hashes welcome gifts are kept by (prepza_common.auth.person_hash), so nobody with a
    # list of addresses can match them.
    person_hash_key: str

    @model_validator(mode="after")
    def paddle_keys_match_the_environment(self) -> "Settings":
        # Names the setting, never its value.
        checks = (
            ("PADDLE_API_KEY", self.paddle_api_key, PADDLE_KEY_PREFIXES),
            ("PADDLE_CLIENT_TOKEN", self.paddle_client_token, PADDLE_TOKEN_PREFIXES),
        )

        for name, value, prefixes in checks:
            if value and not value.startswith(prefixes[self.paddle_environment]):
                raise ValueError(f"{name} isn't a Paddle {self.paddle_environment} one")

        return self


settings = Settings()
