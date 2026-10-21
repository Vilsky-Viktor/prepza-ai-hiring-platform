import json

from babel import Locale
from babel.numbers import format_currency, format_decimal, get_currency_precision
from prepza_common.constants import LANGUAGES

from app.constants.faq import FAQS
from app.constants.help import CURRENCY_SPACING, FAQ_EXAMPLE_CANDIDATES, WHOLE_DECIMALS
from app.constants.privacy import PRIVACY_INTRO, PRIVACY_SECTIONS
from app.constants.terms import TERMS_INTRO, TERMS_SECTIONS
from app.prompts.help import HELP_KNOWLEDGE, PLATFORM_GUIDE

# Catalog fields only Paddle.js needs; they say nothing about prices.
CATALOG_INTERNALS = {"environment", "client_token"}


def guide(limits: dict) -> str:
    """The platform guide, naming `limits` (services/help.py's guide_limits) as they are now."""
    return PLATFORM_GUIDE.format(
        **limits,
        language_count=len(LANGUAGES),
        languages=", ".join(LANGUAGES.values()),
    )


def money(cents: int | None, currency: str, language: str) -> str:
    """An amount in the currency's smallest unit (cents; yen and won themselves) as `language`
    writes it in `currency` ("$5", "5 €", "£2.25", "¥750"), without decimals when it's whole, as
    the site does; empty when billing didn't answer."""
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
    return CURRENCY_SPACING.sub("\u00a0", written)


def grouped(number: int | str, language: str) -> str:
    """A number as `language` groups its digits ("1,500", "1.500"), in the digits the FAQ is
    written in, as the site writes it; empty stays empty."""
    if number == "":
        return ""

    return format_decimal(number, locale=language, numbering_system="latn")


def faq_values(catalog: dict | None, language: str) -> dict:
    """What the FAQ's answers name: prices from billing, and the number of languages."""
    prices = catalog or {}
    candidate = prices.get("candidate_credits", "")
    currency = prices.get("currency", "USD")
    standard = prices.get("candidate_cents_max")

    return {
        "count": len(LANGUAGES),
        "candidate": grouped(candidate, language),
        # In the catalog's currency: the standard and the cheapest price of a candidate, what
        # the example company pays a year, and nothing (automatic top-up's subscription).
        "candidate_price": money(standard, currency, language),
        "cheapest_price": money(prices.get("candidate_cents_min"), currency, language),
        "example_year_price": money(
            standard * FAQ_EXAMPLE_CANDIDATES * 12 if standard else None, currency, language
        ),
        "zero_price": money(0, currency, language),
        "example_candidates": FAQ_EXAMPLE_CANDIDATES,
        "company": grouped(prices.get("welcome_company", ""), language),
        # The candidates a new company's welcome credits cover.
        "company_candidates": (
            prices["welcome_company"] // candidate
            if candidate and "welcome_company" in prices
            else ""
        ),
    }


def faq_items(language: str, catalog: dict | None) -> list[dict]:
    """The FAQ in `language`, its prices filled in."""
    faq = FAQS[language]
    values = faq_values(catalog, language)

    return [
        {
            "key": item["key"],
            "question": item["question"],
            "answer": item["answer"].format(**values),
        }
        for item in faq
    ]


def faq_text(language: str, catalog: dict | None) -> str:
    return "\n\n".join(
        f"Q: {item['question']}\nA: {item['answer']}" for item in faq_items(language, catalog)
    )


def prices_text(catalog: dict | None) -> str:
    """Billing's catalog as it is: its field names say what each number is."""
    if catalog is None:
        return "Not available right now; the pricing page lists every price."

    public = {key: value for key, value in catalog.items() if key not in CATALOG_INTERNALS}

    return json.dumps(public, indent=1)


def legal_text(intro: str, sections: list[dict]) -> str:
    parts = [intro]

    for section in sections:
        parts.append(section["heading"])
        parts.extend(section.get("paragraphs", []))
        parts.extend(f"- {item}" for item in section.get("items", []))

    return "\n".join(parts)


def knowledge(language: str, catalog: dict | None, limits: dict) -> str:
    """What prepza's help answers from: the platform guide, the FAQ in `language`, the prices,
    the terms and the privacy policy. The help chat's prompt holds it, and the in-app assistant
    reads it from GET /help/guide."""
    return HELP_KNOWLEDGE.format(
        guide=guide(limits),
        faq=faq_text(language, catalog),
        prices=prices_text(catalog),
        terms=legal_text(TERMS_INTRO, TERMS_SECTIONS),
        privacy=legal_text(PRIVACY_INTRO, PRIVACY_SECTIONS),
    )
