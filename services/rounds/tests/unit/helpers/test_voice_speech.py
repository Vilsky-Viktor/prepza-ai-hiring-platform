import math
import struct

from testee_common.i18n.i18n import translate

from rounds.constants.voice import SPEECH_RATE
from rounds.constants.voice_phrases import SAVED
from rounds.helpers.voice_speech import (
    clip_key,
    confirmation,
    letters_said,
    ogg_opus,
    ogg_seconds,
    pcm_seconds,
    question_script,
    saved_answer,
    strays,
)
from rounds.schemas.rounds import NextQuestion


def question(text: str, options: list[str], multi: bool = False) -> NextQuestion:
    return NextQuestion(
        question_id="00000000-0000-0000-0000-000000000001",
        number=1,
        text=text,
        options=options,
        multi=multi,
    )


def test_a_question_is_read_with_its_options_and_their_letters():
    found = question_script(question("What is `len([])`?", ["0", "1", "None", "An error"]), "en")

    assert found == "What is len([])? A: 0. B: 1. C: None. D: An error."


def test_code_and_long_examples_are_left_on_screen():
    text = "What does this print?\n\n```python\nprint(1 + 1)\n```"
    long = "x" * 200
    found = question_script(question(text, ["2", "`11`", long, "Nothing"], multi=True), "en")

    assert "print(1 + 1)" not in found and long not in found
    assert found == (
        "What does this print? Look at the example on screen. Pick multiple options for this question. "
        "A: 2. B: shown on screen. C: shown on screen. D: Nothing."
    )


def test_a_confirmation_names_the_options_chosen():
    assert letters_said([1], "en") == "B"
    assert letters_said([3, 0, 2], "en") == "A, C and D"
    assert confirmation([0, 2], "en") == "You chose A and C. Is that right?"


def test_a_saved_answer_names_its_options_letter_in_the_language():
    assert saved_answer(2, "de") == translate(SAVED, "de").format(letter="C")
    assert saved_answer(2, "de").startswith("C")


def test_the_same_text_in_the_same_voice_is_one_clip():
    assert clip_key("m", "v", "en", "Hi") == clip_key("m", "v", "en", "Hi")
    assert clip_key("m", "v", "en", "Hi") != clip_key("m", "v", "de", "Hi")


def page(granule: int) -> bytes:
    return b"OggS\x00\x00" + struct.pack("<q", granule) + b"\x00" * 16


def test_a_clip_plays_for_its_last_sample_less_the_pre_skip():
    head = b"OpusHead\x01\x01" + struct.pack("<H", 312) + b"\x00" * 8
    audio = page(0) + head + page(48_000 * 3 + 312)

    assert ogg_seconds(audio) == 3.0
    assert ogg_seconds(b"not audio") == 0.0


def test_the_speech_models_audio_is_kept_as_ogg_opus_of_the_same_length():
    # Two seconds of a tone, as the model sends it: 16-bit mono PCM.
    samples = [
        int(8000 * math.sin(2 * math.pi * 440 * i / SPEECH_RATE)) for i in range(2 * SPEECH_RATE)
    ]
    pcm = struct.pack(f"<{len(samples)}h", *samples)

    audio = ogg_opus(pcm)

    assert pcm_seconds(pcm) == 2.0
    assert audio.startswith(b"OggS") and b"OpusHead" in audio
    assert abs(ogg_seconds(audio) - 2.0) < 0.05
    assert len(audio) < len(pcm) / 4


def test_a_reading_strays_when_it_adds_words_or_misses_too_many():
    script = "Which index suits range queries? A: B-tree. B: Hash. C: GIN. D: BRIN."

    assert not strays(
        script, "Which index suits range queries? A: B tree. B: Hash. C: GIN. D: BRIN."
    )
    assert strays(script, script + " The correct answer is D.")
    assert strays(script, "Which index suits range queries? A: B-tree. B: Hash.")
