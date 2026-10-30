import asyncio
from types import SimpleNamespace

import pytest
from prepza_common.ai.speech import speech_to_text


def hearing():
    calls = []

    async def create(**arguments):
        calls.append(arguments)

        return SimpleNamespace(text="B")

    return SimpleNamespace(
        audio=SimpleNamespace(transcriptions=SimpleNamespace(create=create))
    ), calls


@pytest.mark.parametrize(
    ("keywords", "sent"),
    [
        # Words it's likely to hear, when there are any.
        (["A", "B", "Mean"], {"keywords": ["A", "B", "Mean"]}),
        (None, {}),
        ([], {}),
    ],
)
def test_a_recording_is_heard_in_its_language_with_the_words_it_may_hear(keywords, sent):
    client, calls = hearing()

    asyncio.run(speech_to_text(client, "m", "a.ogg", b"OggS", "audio/ogg", "de", keywords))

    [arguments] = calls
    assert arguments.pop("languages") == ["de"]
    assert arguments.pop("file") == ("a.ogg", b"OggS", "audio/ogg")
    assert arguments.pop("model") == "m"
    assert arguments == sent
