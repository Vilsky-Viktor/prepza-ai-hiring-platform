from importlib import import_module

from prepza_common.config.constants import DEFAULT_LANGUAGE, LANGUAGES


def with_english(faq: list[dict], english: list[dict]) -> list[dict]:
    """The FAQ in English's order, each question translated when it is, in English until then."""
    translated = {item["key"]: item for item in faq}

    return [translated.get(item["key"], item) for item in english]


_ENGLISH = import_module(f"app.constants.faq.{DEFAULT_LANGUAGE}").FAQ

# Every language's FAQ, by code.
FAQS = {
    code: with_english(import_module(f"app.constants.faq.{code}").FAQ, _ENGLISH)
    for code in LANGUAGES
}
