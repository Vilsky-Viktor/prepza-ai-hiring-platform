from testee_common.i18n.i18n import translate
from testee_common.i18n.money import money
from testee_common.i18n.plurals import plurals

from billing.constants.products import AGREED_TERMS


def agreed_terms(price: int, currency: str, threshold: int, language: str) -> str:
    """An automatic top-up's terms as its buyer agreed to them, in their language ("$50 plus tax
    when the balance falls under 1,500 credits"), for the company's action log."""
    terms = plurals(translate(AGREED_TERMS, language), language, {"threshold": threshold})

    return terms.format(price=money(price, currency, language))
