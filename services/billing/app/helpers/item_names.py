from babel import Locale
from babel.numbers import format_decimal
from prepza_common.config.constants import DEFAULT_LANGUAGE

from app.constants.item_names import CANDIDATES_NAMES


def candidates_name(count: int, language: str) -> str:
    """A top-up's item name as `language` writes it ("1,000 candidates", "1.000 Kandidaten",
    "候補者 1,000 人"): the number with its grouping, the noun in its plural form for that number.
    A language we don't name gets English."""
    if language not in CANDIDATES_NAMES:
        language = DEFAULT_LANGUAGE

    forms = CANDIDATES_NAMES[language]
    form = forms.get(Locale.parse(language).plural_form(count), forms["other"])

    return form.format(count=format_decimal(count, locale=language, numbering_system="latn"))
