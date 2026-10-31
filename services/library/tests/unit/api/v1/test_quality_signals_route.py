"""/internal/questions/signals: every company's flagged and replaced questions, so only
generation's weekly pattern job may read them; any other service is refused."""

import pytest
from testee_common.auth.service_auth import issue_token
from testee_common.http.http import bearer

from library.schemas.quality_report import QualitySignalOut
from library.services import quality_signals

SECRET = "test-secret-that-is-at-least-32-bytes"
SIGNAL = QualitySignalOut(
    flag="rewrite",
    text="Which one is right?",
    options=[{"answer": "This one", "correct": True}, {"answer": "That one", "correct": False}],
    answers=40,
    correct=4.0,
    option_picks={"This one": 4, "That one": 36},
    timeouts=1,
    reasons={"unclear": 2},
    likes=0,
    dislikes=3,
)


@pytest.fixture
def recent(monkeypatch):
    asked = []

    async def found(days):
        asked.append(days)

        return [SIGNAL]

    monkeypatch.setattr(quality_signals, "recent", found)

    return asked


def test_generation_reads_last_weeks_signals_without_ids(client, recent):
    response = client.get(
        "/internal/questions/signals",
        params={"days": 7},
        headers=bearer(issue_token("generation", "library", SECRET)),
    )

    assert response.status_code == 200
    assert recent == [7]
    [sent] = response.json()
    assert sorted(sent) == [
        "answers",
        "correct",
        "dislikes",
        "flag",
        "likes",
        "new_options",
        "new_text",
        "option_picks",
        "options",
        "reasons",
        "text",
        "timeouts",
    ]


@pytest.mark.parametrize("caller", ["rounds", "companies", "assistant", "api"])
def test_any_other_service_is_refused(client, recent, caller):
    refused = client.get(
        "/internal/questions/signals", headers=bearer(issue_token(caller, "library", SECRET))
    )

    assert refused.status_code == 403
    assert refused.json()["detail"] == "Not allowed"
    assert recent == []


def test_without_a_service_token_its_refused(client, recent):
    assert client.get("/internal/questions/signals").status_code in (401, 403)
    assert recent == []


def test_more_than_a_month_back_is_refused(client, recent):
    refused = client.get(
        "/internal/questions/signals",
        params={"days": 32},
        headers=bearer(issue_token("generation", "library", SECRET)),
    )

    assert refused.status_code == 422
    assert recent == []
