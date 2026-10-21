import re
from enum import StrEnum


class Currency(StrEnum):
    """The currencies prices are in: EUR in the EU and nearby, GBP in the UK, USD elsewhere."""

    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"


# A visitor's country: two letters, as Google's load balancer gives it ("XX" when it doesn't
# know).
COUNTRY = re.compile(r"^[A-Za-z]{2}$")
UNKNOWN_COUNTRY = "XX"

# Where the visitor's country isn't known, or is neither of those below.
DEFAULT_CURRENCY = Currency.USD

# The 27 EU states, plus Iceland, Liechtenstein, Norway and Switzerland: two-letter country codes,
# as Google's load balancer and Paddle write them.
EUR_COUNTRIES = (
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FR", "GR", "HR", "HU", "IE",
    "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK",
    "IS", "LI", "NO", "CH",
)  # fmt: skip
GBP_COUNTRIES = ("GB",)

# Each currency but the default, and the countries whose visitors see it.
COUNTRY_CURRENCIES = {Currency.EUR: EUR_COUNTRIES, Currency.GBP: GBP_COUNTRIES}


class ChoiceOwner(StrEnum):
    """Who chose a currency: a company pays in it, a person sees prices in it."""

    COMPANY = "company"
    USER = "user"
