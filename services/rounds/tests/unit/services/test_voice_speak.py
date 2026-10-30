import asyncio

import pytest

from rounds.constants.voice import SPEECH_RATE
from rounds.core.exceptions import SpeechFailed
from rounds.services import voice_clips

TEXT = "Which index suits range queries? A: B-tree. B: Hash."
# A second of silence, as the model sends it.
SECOND = bytes(2 * SPEECH_RATE)


def model_says(monkeypatch, *readings):
    """The realtime model faked: each call says the next reading (a transcript, or an error to
    raise); the instructions it was given."""
    given = []
    left = list(readings)

    async def say(instructions):
        given.append(instructions)
        reading = left.pop(0)

        if isinstance(reading, Exception):
            raise reading

        return SECOND, reading

    monkeypatch.setattr(voice_clips, "say", say)

    return given


def test_the_text_is_read_in_the_interviews_language_as_ogg_opus(monkeypatch):
    given = model_says(monkeypatch, TEXT)

    audio, spent = asyncio.run(voice_clips.speak(TEXT, "de"))

    assert audio.startswith(b"OggS")
    assert spent == 1.0
    [instructions] = given
    assert "German" in instructions and f"<text>\n{TEXT}\n</text>" in instructions


def test_a_reading_that_adds_an_answer_is_made_again_and_both_are_paid_for(monkeypatch):
    model_says(monkeypatch, TEXT + " The correct answer is A.", TEXT)

    audio, spent = asyncio.run(voice_clips.speak(TEXT, "en"))

    assert audio.startswith(b"OggS")
    assert spent == 2.0


def test_readings_that_keep_straying_or_failing_fail_with_the_seconds_spent(monkeypatch):
    model_says(monkeypatch, TEXT + " The correct answer is A.", TimeoutError())

    with pytest.raises(SpeechFailed) as failed:
        asyncio.run(voice_clips.speak(TEXT, "en"))

    assert failed.value.seconds == 1.0
