from pathlib import Path

from prepza_common.i18n.translations import TRANSLATIONS, raised_messages


def test_every_message_the_service_raises_is_translated():
    raised = raised_messages(Path(__file__).resolve().parents[2] / "src" / "assistant")

    for language, messages in TRANSLATIONS.items():
        assert sorted(raised - set(messages)) == [], language
