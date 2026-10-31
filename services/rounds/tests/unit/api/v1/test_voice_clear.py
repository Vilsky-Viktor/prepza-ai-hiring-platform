# Voice mode's clear answers: a choice of one option on a single-answer question, saved at once
# with "B, saved.", and each answer's timed stages (test_voice.py has the rest).
from types import SimpleNamespace

import pytest
from testee_common.i18n.i18n import translate

from rounds.constants.voice_phrases import SAVED
from rounds.schemas.voice import VoiceMatch
from rounds.services import voice_match, voice_session
from tests.unit.api.v1 import test_voice

OGG = test_voice.OGG
SPOKEN = test_voice.SPOKEN
section = test_voice.section
# The candidate's voice interview, as test_voice.py's tests get it.
voice = test_voice.voice


@pytest.mark.parametrize(
    ("heard", "letters", "correct", "intent", "picks", "clear", "matched"),
    [
        # Only letters: read by code, a single one clear, several on a multi-answer question not.
        ("Antwort C.", ["B"], [1], "choose", [2], True, False),
        ("B und D", ["B"], [1, 3], "choose", [1, 3], False, False),
        # The model's choice: clear only as one option on a single-answer question.
        ("die zweite", ["B"], [1], "choose", [1], True, True),
        ("die zweite und die letzte", ["B", "D"], [1, 3], "choose", [1, 3], False, True),
    ],
)
def test_a_choice_is_clear_only_as_one_option_on_a_single_answer_question(
    client, voice, monkeypatch, heard, letters, correct, intent, picks, clear, matched
):
    voice.heard = heard
    for index, option in enumerate(voice.row.questions[0]["options"]):
        option["correct"] = index in correct

    async def read_match(question, said, waiting, language):
        voice.matched.append(said)

        return VoiceMatch(intent="choose", letters=letters), {"input_tokens": 300}

    monkeypatch.setattr(voice_match, "read_match", read_match)

    response = client.post(f"/sessions/{voice.row.id}/voice/answers", content=SPOKEN, headers=OGG)

    assert response.json() == {"heard": heard, "intent": intent, "picks": picks, "clear": clear}
    assert bool(voice.matched) == matched


def test_a_turns_stages_are_logged_with_ids_only(client, voice, caplog):
    caplog.set_level("INFO")

    client.post(f"/sessions/{voice.row.id}/voice/answers", content=SPOKEN, headers=OGG)

    [line] = [r.getMessage() for r in caplog.records if r.getMessage().startswith("Voice answer")]
    assert line.startswith(f"Voice answer {voice.row.id}: choose by model, transcribe;dur=")
    assert "match;dur=" in line and "total;dur=" in line


def test_a_saved_answer_names_its_option_in_the_interviews_language(client, voice, monkeypatch):
    read_aloud = []

    async def clip_for(row, text, language, company_text):
        read_aloud.append((text, language, company_text))

        return SimpleNamespace(audio=b"OggS saved", seconds=1.0)

    monkeypatch.setattr(voice_session, "clip_for", clip_for)
    base = f"/sessions/{voice.row.id}/voice/saved"

    played = client.get(f"{base}/1")

    assert played.status_code == 200
    assert played.content == b"OggS saved"
    assert read_aloud == [(translate(SAVED, "de").format(letter="B"), "de", False)]
    assert client.get(f"{base}/4").status_code == 422

    voice.row = section(voice=False)

    assert client.get(f"/sessions/{voice.row.id}/voice/saved/1").status_code == 409
