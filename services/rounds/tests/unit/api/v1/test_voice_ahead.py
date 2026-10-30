# Voice mode reading the section's next question aloud ahead (test_voice.py has the rest).
from uuid import uuid4

import pytest
from prepza_common.i18n.i18n import translate

from rounds.constants.voice_phrases import SAVED
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


def read(made: list) -> list:
    """The questions read ahead, the interviewer's phrases left out."""
    return [clip for clip in made if clip[2]]


@pytest.fixture
def ahead(monkeypatch):
    """The clips made ahead: (text, language, company_text) each. The interview has only the
    section on screen, unless a test adds sections after it to `others`."""
    made = []

    async def made_ahead(row, text, language, company_text):
        made.append((text, language, company_text))

    monkeypatch.setattr(voice_session, "made_ahead", made_ahead)

    return made


@pytest.fixture
def others(monkeypatch):
    """The interview's sections after the one on screen, in order."""
    after = []

    async def own_sections(row):
        return [row, *after]

    monkeypatch.setattr(voice_session, "own_sections", own_sections)

    return after


def test_the_next_question_is_read_aloud_ahead_and_nothing_of_it_is_sent(client, voice, ahead):
    voice.row = with_next_question(section())

    response = client.post(f"/sessions/{voice.row.id}/voice/next-question/prepare")

    assert response.status_code == 204
    assert response.content == b""
    assert read(ahead) == [("Which chart shows a distribution? A: Histogram. B: Pie.", "de", True)]


@pytest.mark.parametrize(
    ("row", "status"),
    [
        # The interview's last question: nothing follows it.
        (section(), 204),
        # Never ahead of a question that isn't on the clock, or in click mode, or another's.
        (with_next_question(section(shown=False)), 409),
        (with_next_question(section(voice=False)), 409),
        (with_next_question(section(user_id="someone-else")), 404),
    ],
)
def test_nothing_is_read_ahead_without_a_next_question_on_the_candidates_clock(
    client, voice, ahead, others, row, status
):
    voice.row = row

    assert client.post(f"/sessions/{row.id}/voice/next-question/prepare").status_code == status
    assert read(ahead) == []


def test_after_a_sections_last_question_the_next_sections_first_is_read_ahead(
    client, voice, ahead, others
):
    voice.row = section()
    finished, following = with_next_question(section()), with_next_question(section())
    finished.status = "finished"
    others += [finished, following]

    assert client.post(f"/sessions/{voice.row.id}/voice/next-question/prepare").status_code == 204
    # The running section's first question, never a finished one's.
    assert read(ahead) == [
        ("Which measure ignores outliers best? A: Mean. B: Median. C: Range. D: Mode.", "de", True)
    ]


def test_a_finished_section_reads_nothing_ahead(client, voice, ahead):
    voice.row = with_next_question(section())
    voice.row.status = "finished"

    assert client.post(f"/sessions/{voice.row.id}/voice/next-question/prepare").status_code == 204
    assert ahead == []


def test_a_single_answer_questions_saved_answers_are_made_ahead(client, voice, ahead, others):
    """Each option's "B, saved." in the interview's language, so a clear answer is told at once;
    none for a select-all-that-apply question, which is always confirmed."""
    voice.row = section()

    assert client.post(f"/sessions/{voice.row.id}/voice/next-question/prepare").status_code == 204
    assert [clip for clip in ahead if not clip[2]] == [
        (translate(SAVED, "de").format(letter=letter), "de", False) for letter in "ABCD"
    ]

    ahead.clear()
    voice.row = section()
    for option in voice.row.questions[0]["options"][:2]:
        option["correct"] = True

    assert client.post(f"/sessions/{voice.row.id}/voice/next-question/prepare").status_code == 204
    assert ahead == []
