import pytest
from prepza_common.i18n.plurals import plurals

CREDITS = {
    "en": "{n, plural, one {# credit} other {# credits}}",
    "ru": "{n, plural, one {# кредит} few {# кредита} many {# кредитов} other {# кредита}}",
    "pl": "{n, plural, one {# kredyt} few {# kredyty} many {# kredytów} other {# kredytu}}",
    "ar": (
        "{n, plural, zero {# رصيد} one {رصيد واحد} two {رصيدان} few {# أرصدة} "
        "many {# رصيدًا} other {# رصيد}}"
    ),
}


@pytest.mark.parametrize(
    ("language", "count", "written"),
    [
        ("en", 1, "1 credit"),
        ("en", 1500, "1,500 credits"),
        ("ru", 1, "1 кредит"),
        ("ru", 3, "3 кредита"),
        ("ru", 1500, "1 500 кредитов"),
        ("ru", 21, "21 кредит"),
        ("pl", 1, "1 kredyt"),
        ("pl", 22, "22 kredyty"),
        ("pl", 5000, "5\u00a0000 kredytów"),
        ("ar", 1, "رصيد واحد"),
        ("ar", 2, "رصيدان"),
        ("ar", 3, "3 أرصدة"),
        ("ar", 11, "11 رصيدًا"),
        ("ar", 100, "100 رصيد"),
    ],
)
def test_each_language_writes_the_count_in_its_own_plural_form(language, count, written):
    assert plurals(CREDITS[language], language, {"n": count}) == written


def test_an_exact_case_comes_first_and_the_rest_of_the_text_stays():
    text = "{price} for {n, plural, =1 {one credit} other {# credits}}, {m, plural, other {#}}"

    assert plurals(text, "en", {"n": 1}) == "{price} for one credit, {m, plural, other {#}}"
