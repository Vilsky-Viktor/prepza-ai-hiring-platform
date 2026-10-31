from testee_common.config.constants import LANGUAGES

from ats.helpers.ats import result_comment
from ats.templates.comments import COMMENTS


def test_a_german_interview_gets_the_note_in_german():
    text = result_comment("Buchhalter", 82, True, True, "https://testee.ai/s/1", "de")

    assert text.splitlines() == [
        "testee: Buchhalter",
        "Ergebnis: 82 % (bestanden)",
        "Hinweise auf Auffälligkeiten: ja, vom Browser des Kandidaten gemeldet; ein Grund, auf der Auswertung genauer hinzusehen, kein Beweis.",
        "Die Entscheidung trifft ein Mensch: nicht automatisch anhand dieses Ergebnisses ablehnen.",
        "Auswertung: https://testee.ai/s/1",
    ]


def test_an_unknown_or_missing_language_gets_the_note_in_english():
    english = result_comment("A", None, False, False, "x", "en")

    assert result_comment("A", None, False, False, "x", "xx") == english
    assert result_comment("A", None, False, False, "x", None) == english
    assert "Finished; the grade is on the scorecard." in english


def test_every_language_has_every_text_with_the_same_fields():
    assert set(COMMENTS) == set(LANGUAGES)

    for language, texts in COMMENTS.items():
        assert set(texts) == set(COMMENTS["en"]), language

        for key, text in texts.items():
            assert text.strip(), (language, key)

        assert "{grade}" in texts["grade"] and "{result}" in texts["grade"], language
        assert "{link}" in texts["scorecard"], language
