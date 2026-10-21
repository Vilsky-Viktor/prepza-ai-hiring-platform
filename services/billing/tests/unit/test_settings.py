"""Paddle's sandbox and live accounts never mix: a key or token of the other environment stops
billing from starting."""

import pytest
from pydantic import ValidationError

from app.config.settings import Settings


@pytest.mark.parametrize(
    ("environment", "api_key", "client_token"),
    [
        ("sandbox", "pdl_sdbx_apikey_1", "test_1"),
        ("production", "pdl_live_apikey_1", "live_1"),
        # Not set yet: nothing is sold, nothing to mix.
        ("production", "", ""),
    ],
)
def test_keys_of_the_environment_are_accepted(environment, api_key, client_token):
    settings = Settings(
        paddle_environment=environment, paddle_api_key=api_key, paddle_client_token=client_token
    )

    assert settings.paddle_environment == environment


@pytest.mark.parametrize(
    ("environment", "api_key", "client_token", "refused"),
    [
        ("production", "pdl_sdbx_apikey_1", "live_1", "PADDLE_API_KEY isn't a Paddle production one"),
        ("production", "pdl_live_apikey_1", "test_1", "PADDLE_CLIENT_TOKEN isn't a Paddle production one"),
        ("sandbox", "pdl_live_apikey_1", "test_1", "PADDLE_API_KEY isn't a Paddle sandbox one"),
        ("sandbox", "pdl_sdbx_apikey_1", "live_1", "PADDLE_CLIENT_TOKEN isn't a Paddle sandbox one"),
    ],
)  # fmt: skip
def test_a_key_of_the_other_environment_stops_billing_starting(
    environment, api_key, client_token, refused
):
    with pytest.raises(ValidationError) as error:
        Settings(
            paddle_environment=environment,
            paddle_api_key=api_key,
            paddle_client_token=client_token,
        )

    assert refused in str(error.value)
    # The key itself is never repeated in the error.
    assert api_key not in str(error.value)


def test_an_unknown_environment_stops_billing_starting():
    with pytest.raises(ValidationError):
        Settings(paddle_environment="live")
