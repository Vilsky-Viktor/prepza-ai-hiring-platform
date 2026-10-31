# An amount of money as a language writes it: site's FAQ and help chat's knowledge,
# notifications' emails.
# Needs the `money` extra (babel).
from babel import Locale
from babel.numbers import format_currency, get_currency_precision
from testee_common.config.constants import CURRENCY_SPACING, WHOLE_DECIMALS


def money(cents: int | None, currency: str, language: str) -> str:
    """An amount in the currency's smallest unit (cents; yen and won themselves) as `language`
    writes it in `currency` ("$5", "5 €", "£2.25", "¥750"), without decimals when it's whole, as
    the site does; empty for none."""
    if cents is None:
        return ""

    units = 10 ** get_currency_precision(currency)
    whole = cents % units == 0
    pattern = Locale.parse(language).currency_formats["standard"].pattern

    written = format_currency(
        cents / units,
        currency,
        format=WHOLE_DECIMALS.sub("", pattern) if whole else None,
        locale=language,
        currency_digits=not whole,
        numbering_system="latn",
    )

    # A symbol in letters ("CHF") is kept apart from the number, as CLDR's currency spacing
    # (and so the site) does; babel leaves it joined.
    return CURRENCY_SPACING.sub(" ", written)
