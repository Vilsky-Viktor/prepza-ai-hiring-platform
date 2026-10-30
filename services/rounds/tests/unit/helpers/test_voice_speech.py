import struct

from rounds.helpers.voice_speech import (
    clip_key,
    confirmation,
    letters_said,
    ogg_seconds,
    question_script,
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
        "What does this print? Look at the example on screen. Choose every option that applies. "
        "A: 2. B: shown on screen. C: shown on screen. D: Nothing."
    )


def test_a_confirmation_names_the_options_chosen():
    assert letters_said([1], "en") == "B"
    assert letters_said([3, 0, 2], "en") == "A, C and D"
    assert confirmation([0, 2], "en") == "You chose A and C. Is that right?"


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
