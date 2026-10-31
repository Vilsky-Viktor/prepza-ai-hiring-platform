from pathlib import Path

from testee_common.i18n.translations import TRANSLATIONS, raised_messages

from companies.constants.invites import COMPANY_NAME_TAKEN, TOO_MANY_COMPANIES, TOO_MANY_INTERVIEWS


def test_limit_messages_have_translations():
    for language in TRANSLATIONS.values():
        assert TOO_MANY_COMPANIES in language
        assert TOO_MANY_INTERVIEWS in language
        assert COMPANY_NAME_TAKEN in language


def test_every_message_the_service_raises_is_translated():
    raised = raised_messages(Path(__file__).resolve().parents[2] / "src")

    for language, messages in TRANSLATIONS.items():
        assert sorted(raised - set(messages)) == [], language
