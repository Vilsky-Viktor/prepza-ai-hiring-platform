import re
from enum import StrEnum


class Currency(StrEnum):
    """The currencies prices are in: a country's own where billing sells in it, USD elsewhere."""

    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CAD = "CAD"
    AUD = "AUD"
    ILS = "ILS"
    PLN = "PLN"
    JPY = "JPY"
    KRW = "KRW"
    TWD = "TWD"
    HKD = "HKD"
    CHF = "CHF"
    THB = "THB"
    SGD = "SGD"
    INR = "INR"


# A visitor's country: two letters, as Google's load balancer gives it ("XX" when it doesn't
# know).
COUNTRY = re.compile(r"^[A-Za-z]{2}$")
UNKNOWN_COUNTRY = "XX"

# A row's currency must be one of these (the database checks it).
CURRENCY_CHECK = "currency IN (" + ", ".join(f"'{code}'" for code in Currency) + ")"
# The same for an automatic top-up's agreed price.
PRICE_CURRENCY_CHECK = "price_" + CURRENCY_CHECK

# Where the visitor's country isn't known, or is neither of those below.
DEFAULT_CURRENCY = Currency.USD

# The EU states but Poland (which has its own), plus Iceland, Liechtenstein and Norway:
# two-letter country codes, as Google's load balancer and Paddle write them.
EUR_COUNTRIES = (
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FR", "GR", "HR", "HU", "IE",
    "IT", "LT", "LU", "LV", "MT", "NL", "PT", "RO", "SE", "SI", "SK",
    "IS", "LI", "NO",
)  # fmt: skip

# Each currency but the default, and the countries whose visitors see it.
COUNTRY_CURRENCIES = {
    Currency.EUR: EUR_COUNTRIES,
    Currency.GBP: ("GB",),
    Currency.CAD: ("CA",),
    Currency.AUD: ("AU",),
    Currency.ILS: ("IL",),
    Currency.PLN: ("PL",),
    Currency.JPY: ("JP",),
    Currency.KRW: ("KR",),
    Currency.TWD: ("TW",),
    Currency.HKD: ("HK",),
    Currency.CHF: ("CH",),
    Currency.THB: ("TH",),
    Currency.SGD: ("SG",),
    Currency.INR: ("IN",),
}


class ChoiceOwner(StrEnum):
    """Who chose a currency: a company pays in it, a person sees prices in it."""

    COMPANY = "company"
    USER = "user"
