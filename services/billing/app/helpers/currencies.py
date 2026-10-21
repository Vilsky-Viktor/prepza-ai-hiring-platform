from app.constants.currencies import (
    COUNTRY,
    COUNTRY_CURRENCIES,
    DEFAULT_CURRENCY,
    UNKNOWN_COUNTRY,
    Currency,
)


def known_country(country: str | None) -> bool:
    return bool(country and COUNTRY.match(country) and country.upper() != UNKNOWN_COUNTRY)


def currency_for(country: str | None) -> Currency:
    """The currency a visitor from `country` (a two-letter code, any case) sees and pays in."""
    code = (country or "").upper()

    return next(
        (currency for currency, countries in COUNTRY_CURRENCIES.items() if code in countries),
        DEFAULT_CURRENCY,
    )
