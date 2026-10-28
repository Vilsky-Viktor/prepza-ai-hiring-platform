"""The checks a proposed pattern passes before it's stored (services/patterns.py, rejection):
general wording only, nothing quoted from the questions it came from, and short."""

import pytest
from prepza_common.ai.sets import OptionIn

from generation.constants.patterns import DENIED_TERMS, MAX_PATTERN_CHARS
from generation.helpers.patterns import names_something, quotes_input
from generation.schemas.patterns import ProposedPattern, QualitySignal
from generation.services.patterns import rejection

GENERAL = "Two options say the same thing in different words."


def signal(text="Which of these keeps the ledger balanced at the end of the month?", **values):
    options = values.pop(
        "options",
        [
            OptionIn(answer="Posting both sides of every entry", correct=True),
            OptionIn(answer="Posting only the larger side", correct=False),
        ],
    )

    return QualitySignal(
        flag=values.pop("flag", "rewrite"),
        text=text,
        options=options,
        answers=10,
        correct=0.5,
        option_picks={},
        timeouts=0,
        reasons={},
        likes=0,
        dislikes=0,
        **values,
    )


def proposed(text):
    return ProposedPattern(text=text, questions=[1, 2], same_as=None)


@pytest.mark.parametrize("term", DENIED_TERMS)
def test_a_pattern_naming_a_technology_field_or_role_is_rejected(term):
    assert names_something(f"the scenario leaves out the {term} that decides it.") == (
        f"names '{term}'"
    )


def test_a_denied_word_is_found_in_any_case_and_as_the_start_of_a_longer_word():
    assert names_something("Questions about Programming leave out the version.") == (
        "names 'program'"
    )


def test_a_capitalized_word_inside_a_sentence_is_rejected_as_a_name():
    assert names_something("The scenario leaves out which Acme plan is meant.") == (
        "has a capitalized word"
    )


@pytest.mark.parametrize("mark", [".", "!", "?", ":"])
def test_a_capitalized_word_starting_a_sentence_is_allowed(mark):
    text = f"The scenario leaves out a detail{mark} Every option then fits."

    assert names_something(text) is None


def test_a_name_in_a_second_sentence_is_still_rejected():
    text = "The scenario leaves out a detail. Every option fits Acme."

    assert names_something(text) == "has a capitalized word"


def test_a_general_pattern_passes_every_check():
    assert names_something(GENERAL) is None
    assert rejection(proposed(GENERAL), [signal()]) is None


def test_six_words_in_a_row_from_a_question_are_a_quote():
    quoting = "Questions ask which of these keeps the ledger balanced, and more."

    assert quotes_input(quoting, [signal()])
    assert rejection(proposed(quoting), [signal()]) == "quotes a question"


def test_five_words_in_a_row_are_not_a_quote():
    assert not quotes_input("Questions ask which of these keeps nothing in order.", [signal()])


def test_a_quote_ignores_case_and_punctuation():
    assert quotes_input("WHICH, of these keeps the ledger: balanced.", [signal()])


def test_quoting_an_option_is_rejected():
    assert quotes_input("An option says posting both sides of every entry again.", [signal()])


def test_quoting_the_replacement_or_its_options_is_rejected():
    replaced = signal(
        new_text="What does a balanced ledger need at the close of a period?",
        new_options=[OptionIn(answer="Matching debits and credits for each entry", correct=True)],
    )

    assert quotes_input("It asks what does a balanced ledger need here.", [replaced])
    assert quotes_input("One says matching debits and credits for each entry.", [replaced])


def test_any_of_the_input_questions_counts():
    other = signal("How many approvals does a purchase over the limit need first?")

    assert quotes_input("It asks how many approvals does a purchase need.", [signal(), other])


def test_a_pattern_longer_than_the_limit_is_rejected():
    long = "a" * (MAX_PATTERN_CHARS + 1)

    assert rejection(proposed(long), [signal()]) == "too long"
    assert rejection(proposed(GENERAL[:MAX_PATTERN_CHARS]), [signal()]) is None
