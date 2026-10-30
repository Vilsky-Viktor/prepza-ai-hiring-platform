import pytest

from rounds.helpers.voice_letters import plain_letters


@pytest.mark.parametrize(
    ("said", "language", "expected"),
    [
        # Letters alone, after a word that can't change them, or several joined by "and".
        ("B", "en", [1]),
        ("B.", "en", [1]),
        ("b!", "en", [1]),
        ("Option B.", "en", [1]),
        ("answer: C", "en", [2]),
        ("Letter D", "en", [3]),
        ("B and D", "en", [1, 3]),
        ("a, b, d", "en", [0, 1, 3]),
        ("A, B, and D", "en", [0, 1, 3]),
        ("option A and option D", "en", [0, 3]),
        ("D and D", "en", [3]),
        ("la B y la D", "es", [1, 3]),
        ("la respuesta D.", "es", [3]),
        ("Antwort C", "de", [2]),
        ("B und D", "de", [1, 3]),
        ("l’option B", "fr", [1]),
        ("la réponse C", "fr", [2]),
        ("alternativa C", "pt", [2]),
        ("B e D", "pt", [1, 3]),
        ("la B e la D", "it", [1, 3]),
        # Anything else is the model's: other words, a question, a pause, a change of mind.
        ("B is wrong, I mean C", "en", None),
        ("not A", "en", None),
        ("between B and C... C", "en", None),
        ("A? No.", "en", None),
        ("B?", "en", None),
        ("A. B.", "en", None),
        ("B or C", "en", None),
        ("A, maybe D", "en", None),
        ("the first one", "en", None),
        ("bee", "en", None),
        ("a b", "en", None),
        ("la B no, la C", "es", None),
        ("nicht A", "de", None),
        ("pas la A", "fr", None),
        ("é a C", "pt", None),
        ("a b", "pt", None),
        ("letra bê", "pt", None),
        ("non la A, la C", "it", None),
        # Another language's words aren't this one's.
        ("Antwort C", "en", None),
        ("", "en", None),
    ],
)
def test_only_plain_letters_are_read_without_the_model(said, language, expected):
    assert plain_letters(said, 4, language) == expected


def test_a_letter_past_the_options_is_the_models():
    assert plain_letters("D", 3, "en") is None
    assert plain_letters("B and D", 3, "en") is None
    assert plain_letters("C", 3, "en") == [2]
