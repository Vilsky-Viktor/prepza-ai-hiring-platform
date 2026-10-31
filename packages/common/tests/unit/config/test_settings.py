import pytest
from pydantic import ValidationError
from testee_common.config.settings import ServiceSettings


def test_the_auth_emulator_is_allowed_only_for_a_demo_project():
    demo = ServiceSettings(
        firebase_project_id="demo-testee", firebase_auth_emulator_host="auth:9199"
    )

    assert demo.firebase_auth_emulator_host == "auth:9199"
    assert ServiceSettings(firebase_project_id="testee-prod").firebase_auth_emulator_host == ""

    with pytest.raises(ValidationError):
        ServiceSettings(firebase_project_id="testee-prod", firebase_auth_emulator_host="auth:9199")


class WithSecret(ServiceSettings):
    """A service's settings: a secret beside a setting that must be a number."""

    api_key: str
    port: int


def test_a_refused_setting_never_repeats_the_values_given(monkeypatch):
    # From the environment, as services read them at start-up.
    monkeypatch.setenv("FIREBASE_PROJECT_ID", "testee-prod")
    monkeypatch.setenv("API_KEY", "sk-very-secret-value")
    monkeypatch.setenv("PORT", "not-a-port")

    with pytest.raises(ValidationError) as error:
        WithSecret()

    message = str(error.value)

    # Which setting is wrong is said; no value given is repeated.
    assert "port" in message
    assert "sk-very-secret-value" not in message
    assert "not-a-port" not in message
    assert "testee-prod" not in message
