from pathlib import Path

from prepza_common.i18n.translations import TRANSLATIONS, raised_messages

from generation.constants.generation import GENERATIONS_PAUSED


def test_messages_users_see_have_translations():
    for language in TRANSLATIONS.values():
        assert GENERATIONS_PAUSED in language


def test_every_message_the_service_raises_is_translated():
    raised = raised_messages(Path(__file__).resolve().parents[2] / "src")

    for language, messages in TRANSLATIONS.items():
        assert sorted(raised - set(messages)) == [], language
