import pytest
from prepza_common.ai.spoken_words import word_errors, words


def test_words_ignore_case_punctuation_and_hyphens():
    assert words("Which index? A: B-tree.") == ["which", "index", "a", "b", "tree"]


@pytest.mark.parametrize(
    ("heard", "rate", "added"),
    [
        # Read as written, the hyphen aside.
        ("Which index? A: B tree. B: Hash.", 0.0, 0),
        # An answer put in after the options.
        ("Which index? A: B-tree. B: Hash. The answer is A.", 4 / 7, 4),
        # A greeting put in before the question.
        ("Sure, here it is. Which index? A: B-tree. B: Hash.", 4 / 7, 4),
        # An option left out: words missing, nothing added.
        ("Which index? A: B-tree.", 2 / 7, 0),
        # Two words misheard, none added.
        ("Which index? A: Bee tree. Be: Hash.", 2 / 7, 0),
    ],
)
def test_word_errors_count_changes_and_the_longest_run_added(heard, rate, added):
    found_rate, found_added = word_errors("Which index? A: B-tree. B: Hash.", heard)

    assert found_rate == pytest.approx(rate)
    assert found_added == added


def test_nothing_said_against_nothing_to_say_is_no_error():
    assert word_errors("", "") == (0.0, 0)
