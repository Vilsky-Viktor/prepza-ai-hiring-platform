from pathlib import Path

from prepza_common.i18n.translations import TRANSLATIONS, raised_messages

from rounds.constants.rounds import CHAT_FAILED


def test_messages_users_see_have_translations():
    for language in TRANSLATIONS.values():
        assert CHAT_FAILED in language


def test_every_message_the_service_raises_is_translated():
    raised = raised_messages(Path(__file__).resolve().parents[2] / "src")

    for language, messages in TRANSLATIONS.items():
        assert sorted(raised - set(messages)) == [], language
