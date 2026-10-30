from babel.numbers import format_decimal
from prepza_common.i18n.i18n import translate
from prepza_common.i18n.money import money

from billing.constants.products import AGREED_TERMS


def agreed_terms(price: int, currency: str, threshold: int, language: str) -> str:
    """An automatic top-up's terms as its buyer agreed to them, in their language ("$50 plus tax
    when the balance falls under 1,500 credits"), for the company's action log."""
    return translate(AGREED_TERMS, language).format(
        price=money(price, currency, language),
        threshold=format_decimal(threshold, locale=language, numbering_system="latn"),
    )
