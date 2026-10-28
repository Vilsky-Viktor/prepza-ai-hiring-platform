import pytest
from pydantic import ValidationError

from assistant.config import Settings


def test_the_assistant_wont_start_without_firebases_web_key(monkeypatch):
    monkeypatch.setenv("FIREBASE_WEB_API_KEY", "")

    with pytest.raises(ValidationError, match="firebase_web_api_key"):
        Settings()
