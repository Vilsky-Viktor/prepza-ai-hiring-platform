# Voice mode reading the section's next question aloud ahead (test_voice.py has the rest).
from uuid import uuid4

import pytest

from rounds.models.sessions import Session
from rounds.services import voice_session
from tests.unit.api.v1 import test_voice

section = test_voice.section
# The candidate's voice interview, as test_voice.py's tests get it.
voice = test_voice.voice


def with_next_question(row: Session) -> Session:
    row.questions = [
        *row.questions,
        {
            "id": str(uuid4()),
            "text": "Which chart shows a distribution?",
            "options": [
                {"answer": "Histogram", "correct": True},
                {"answer": "Pie", "correct": False},
            ],
            "seconds": 60,
        },
    ]

    return row


@pytest.fixture
def ahead(monkeypatch):
    """The clips made ahead: (text, language, company_text) each."""
    made = []

    async def made_ahead(row, text, language, company_text):
        made.append((text, language, company_text))

    monkeypatch.setattr(voice_session, "made_ahead", made_ahead)

    return made


def test_the_next_question_is_read_aloud_ahead_and_nothing_of_it_is_sent(client, voice, ahead):
    voice.row = with_next_question(section())

    response = client.post(f"/sessions/{voice.row.id}/voice/next-question/prepare")

    assert response.status_code == 204
    assert response.content == b""
    assert ahead == [("Which chart shows a distribution? A: Histogram. B: Pie.", "de", True)]


@pytest.mark.parametrize(
    ("row", "status"),
    [
        # The section's last question: nothing follows it.
        (section(), 204),
        # Never ahead of a question that isn't on the clock, or in click mode, or another's.
        (with_next_question(section(shown=False)), 409),
        (with_next_question(section(voice=False)), 409),
        (with_next_question(section(user_id="someone-else")), 404),
    ],
)
def test_nothing_is_read_ahead_without_a_next_question_on_the_candidates_clock(
    client, voice, ahead, row, status
):
    voice.row = row

    assert client.post(f"/sessions/{row.id}/voice/next-question/prepare").status_code == status
    assert ahead == []


def test_a_finished_section_reads_nothing_ahead(client, voice, ahead):
    voice.row = with_next_question(section())
    voice.row.status = "finished"

    assert client.post(f"/sessions/{voice.row.id}/voice/next-question/prepare").status_code == 204
    assert ahead == []
