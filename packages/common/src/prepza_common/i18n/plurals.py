# Counted nouns in backend texts (emails, labels) as ICU plurals, as the frontend's messages
# write them: `{count, plural, one {# credit} other {# credits}}`, each language with its own
# CLDR categories. Needs the `money` extra (babel).
import re

from babel import Locale
from babel.numbers import format_decimal

# One plural block whose cases hold plain text (no placeholders inside them).
PLURAL = re.compile(r"\{(\w+), plural,((?:\s*=?\w+\s*\{[^{}]*\})+)\s*\}")
CASE = re.compile(r"(=?\w+)\s*\{([^{}]*)\}")


def plurals(text: str, language: str, counts: dict[str, int]) -> str:
    """`text` with each plural block of a count in `counts` written out: the exact case (`=1`)
    first, else the category `language` uses for the number, else `other`; `#` is the number as
    the language writes it ("1,500", "1.500", "1 500"). Blocks of other names are left as they
    are."""
    rules = Locale.parse(language)

    def written(match: re.Match) -> str:
        name = match.group(1)

        if name not in counts:
            return match.group(0)

        count = counts[name]
        cases = dict(CASE.findall(match.group(2)))
        form = cases.get(f"={count}") or cases.get(rules.plural_form(count)) or cases["other"]

        return form.replace("#", format_decimal(count, locale=language, numbering_system="latn"))

    return PLURAL.sub(written, text)
