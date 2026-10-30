"""The terms the action log keeps with a buyer's agreement: the price and the level in the buyer's
language, the level's noun in the plural form its number takes there."""

import pytest

from billing.helpers.agreed_terms import agreed_terms


@pytest.mark.parametrize(
    ("language", "threshold", "level"),
    [
        ("en", 1, "1 credit"),
        ("en", 1500, "1,500 credits"),
        # Russian and Polish after "under": one, few and many each take their own form.
        ("ru", 1, "ниже 1 кредита"),
        ("ru", 3, "ниже 3 кредитов"),
        ("ru", 21, "ниже 21 кредита"),
        ("ru", 1500, "ниже 1 500 кредитов"),
        ("pl", 1, "poniżej 1 kredytu"),
        ("pl", 22, "poniżej 22 kredytów"),
    ],
)
def test_the_level_is_written_in_the_plural_its_number_takes(language, threshold, level):
    terms = agreed_terms(5000, "USD", threshold, language)

    assert terms.endswith(level)
    assert "{" not in terms
