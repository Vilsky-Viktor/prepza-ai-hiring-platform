from pathlib import Path

from testee_common.i18n.translations import TRANSLATIONS, raised_messages


def test_report_details_message_has_translations():
    # The validator in schemas/feedback.py raises it.
    for language in TRANSLATIONS.values():
        assert "Details are required for this reason." in language
        assert "Title is required" in language


def test_every_message_the_service_raises_is_translated():
    raised = raised_messages(Path(__file__).resolve().parents[2] / "src")

    for language, messages in TRANSLATIONS.items():
        assert sorted(raised - set(messages)) == [], language
