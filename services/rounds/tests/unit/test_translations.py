from pathlib import Path

from prepza_common.i18n.translations import TRANSLATIONS, raised_messages

from rounds.constants import voice_phrases


def test_every_message_the_service_raises_is_translated():
    raised = raised_messages(Path(__file__).resolve().parents[2] / "src")

    for language, messages in TRANSLATIONS.items():
        assert sorted(raised - set(messages)) == [], language


def test_every_phrase_the_interviewer_says_is_translated():
    spoken = {
        text
        for name, text in vars(voice_phrases).items()
        if name.isupper() and isinstance(text, str)
    }

    for language, messages in TRANSLATIONS.items():
        assert sorted(spoken - set(messages)) == [], language
