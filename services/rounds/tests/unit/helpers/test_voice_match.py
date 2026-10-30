import pytest

from rounds.constants.voice import Intent
from rounds.helpers.voice_match import letters_of, match_prompt, obvious, understood
from rounds.schemas.rounds import NextQuestion
from rounds.schemas.voice import VoiceMatch

QUESTION = NextQuestion(
    question_id="00000000-0000-0000-0000-000000000001",
    number=1,
    text="Which measure ignores outliers best?",
    options=["Mean", "Median", "Range", "Mode"],
)


@pytest.mark.parametrize(
    ("intent", "letters", "multi", "waiting", "expected"),
    [
        (Intent.CHOOSE, ["B"], False, [], (Intent.CHOOSE, [1])),
        (Intent.CHOOSE, ["D", "A", "A"], True, [], (Intent.CHOOSE, [0, 3])),
        # A single-answer question takes one option; none is no choice.
        (Intent.CHOOSE, ["A", "B"], False, [], (Intent.UNCLEAR, [])),
        (Intent.CHOOSE, [], False, [], (Intent.UNCLEAR, [])),
        # A yes picks the choice that was waiting, whatever letters the model gave.
        (Intent.CONFIRM, ["C"], False, [1], (Intent.CONFIRM, [1])),
        (Intent.CONFIRM, [], True, [3, 0], (Intent.CONFIRM, [0, 3])),
        (Intent.REJECT, [], False, [1], (Intent.REJECT, [])),
        # Nothing waiting: a yes or a no means nothing.
        (Intent.CONFIRM, [], False, [], (Intent.UNCLEAR, [])),
        (Intent.REJECT, [], False, [], (Intent.UNCLEAR, [])),
        (Intent.UNCLEAR, ["A"], False, [], (Intent.UNCLEAR, [])),
    ],
)
def test_only_what_the_code_can_check_is_taken_from_the_model(
    intent, letters, multi, waiting, expected
):
    match = VoiceMatch(intent=intent, letters=letters)

    assert understood(match, multi, waiting) == expected


def test_the_prompt_tags_the_reply_as_data_and_never_carries_the_answer_key():
    system, user = match_prompt(QUESTION, "the median", [1], "de")

    assert "the median" not in system.content
    assert "<candidate_said>\nthe median\n</candidate_said>" in user.content
    assert "A. Mean\nB. Median\nC. Range\nD. Mode" in user.content
    assert "<waiting_for_confirmation>B</waiting_for_confirmation>" in user.content
    assert "<test_language>German</test_language>" in user.content
    assert "correct" not in user.content


def test_letters_name_options_in_order():
    assert letters_of([3, 0]) == "A, D"


@pytest.mark.parametrize(
    ("said", "waiting", "language", "expected"),
    [
        # A plain yes, in each voice language, confirms the choice waiting.
        ("Yes.", [1], "en", (Intent.CONFIRM, [1])),
        ("Yeah, that’s right!", [3, 0], "en", (Intent.CONFIRM, [0, 3])),
        ("Sí, eso es.", [2], "es", (Intent.CONFIRM, [2])),
        ("Ja, genau.", [2], "de", (Intent.CONFIRM, [2])),
        ("Oui, c'est ça.", [2], "fr", (Intent.CONFIRM, [2])),
        ("Isso mesmo.", [2], "pt", (Intent.CONFIRM, [2])),
        ("Sì.", [2], "it", (Intent.CONFIRM, [2])),
        # A letter alone is that option, also as a new choice while one waits.
        ("B.", [], "en", (Intent.CHOOSE, [1])),
        ("d", [1], "fr", (Intent.CHOOSE, [3])),
        # Everything else is the model's: a yes with nothing waiting, a yes in another language,
        # a yes with more words, a no, a letter with more words, a letter with no option.
        ("Yes.", [], "en", None),
        ("Ja.", [1], "en", None),
        ("Yes, but C", [1], "en", None),
        ("yes I think so", [1], "en", None),
        ("No.", [1], "en", None),
        ("Letter B", [], "en", None),
        ("A and B", [], "en", None),
        ("", [1], "en", None),
    ],
)
def test_a_plain_yes_or_a_letter_alone_is_read_without_the_model(said, waiting, language, expected):
    assert obvious(said, QUESTION, waiting, language) == expected


def test_a_letter_with_no_option_behind_it_goes_to_the_model():
    three = QUESTION.model_copy(update={"options": ["Mean", "Median", "Range"]})

    assert obvious("D", three, [], "en") is None
    assert obvious("C", three, [], "en") == (Intent.CHOOSE, [2])
