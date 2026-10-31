"""A text's language from its script and its common words, among the site's LANGUAGES."""

import re

from testee_common.config.constants import DEFAULT_LANGUAGE
from testee_common.i18n.language_words import (
    KANA,
    LATIN_WORDS,
    PERSIAN_LETTERS,
    RUSSIAN_LETTERS,
    SCRIPT_LANGUAGES,
    SCRIPT_SHARE,
    SCRIPTS,
    UKRAINIAN_LETTERS,
)


def script_of(char: str) -> str | None:
    code = ord(char)

    for script, ranges in SCRIPTS.items():
        if any(start <= code <= end for start, end in ranges):
            return script

    return None


def text_language(
    text: str, fallback: str = DEFAULT_LANGUAGE, unknown: str = DEFAULT_LANGUAGE
) -> str:
    """A text's own language, for callers that don't choose one. A text without letters takes
    `fallback`, the interface's; a Latin-script text with none of the languages' common words
    takes `unknown` (English for a short job title such as "Python developer")."""
    lowered = text.lower()
    counts = {script: 0 for script in SCRIPTS}
    latin = 0

    for char in lowered:
        script = script_of(char)

        if script:
            counts[script] += 1
        elif char.isalpha():
            latin += 1

    letters = latin + sum(counts.values())

    if letters == 0:
        return fallback

    script = max(counts, key=counts.get)

    if counts[script] / letters >= SCRIPT_SHARE:
        return script_language(script, lowered)

    hits = word_hits(lowered)
    best = max(hits, key=hits.get)

    return best if hits[best] > 0 else unknown


def word_hits(text: str, vocabularies: dict[str, set[str]] = LATIN_WORDS) -> dict[str, int]:
    """How many of each Latin-script language's common words the text has: a job description's
    (LATIN_WORDS) by default, a chat message's with the help chat's own words (rounds)."""
    words = re.findall(r"[^\W\d_]+(?:'[^\W\d_]+)?", text.lower())

    return {
        code: sum(1 for word in words if word in vocabulary)
        for code, vocabulary in vocabularies.items()
    }


def script_language(script: str, text: str) -> str:
    """The language a text in a non-Latin script is in."""
    if script in SCRIPT_LANGUAGES:
        return SCRIPT_LANGUAGES[script]

    if script == "arabic":
        return "fa" if any(char in PERSIAN_LETTERS for char in text) else "ar"

    if script == "cjk":
        return "ja" if any(KANA[0] <= ord(char) <= KANA[1] for char in text) else "zh"

    ukrainian = sum(1 for char in text if char in UKRAINIAN_LETTERS)
    russian = sum(1 for char in text if char in RUSSIAN_LETTERS)

    return "uk" if ukrainian > russian else "ru"
