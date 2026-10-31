from pathlib import Path

from testee_common.i18n.translations import TRANSLATIONS, raised_messages


def test_every_message_the_service_raises_is_translated():
    raised = raised_messages(Path(__file__).resolve().parents[2] / "src")

    for language, messages in TRANSLATIONS.items():
        assert sorted(raised - set(messages)) == [], language
