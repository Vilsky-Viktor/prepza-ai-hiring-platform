import re

from rounds.constants.voice import LETTERS
from rounds.constants.voice_letters import AND_WORDS, LETTER_WORDS

# What may end a reply of letters: a full stop or an exclamation mark, said once.
END = re.compile(r"[.!]$")
# Anything that may mean more than a list: a question, a pause, a dash, quotes, brackets.
NOT_PLAIN = re.compile(r"[?¿¡…\"“”«»()\[\]\-–—]|\.\.|\.\s")


def letter_of(item: str, words: frozenset[str], count: int) -> int | None:
    """One option's index from "b" or "option b" (a word of LETTER_WORDS before it); None for
    anything else, or a letter past the question's options."""
    word, _, letter = item.rpartition(" ")

    if word and word not in words:
        return None

    letter = letter.upper()

    return LETTERS.index(letter) if letter in LETTERS[:count] else None


def plain_letters(said: str, count: int, language: str) -> list[int] | None:
    """The options a reply names when it's only their letters (constants/voice_letters.py):
    "B", "Option B.", "B and D", "a, b, d". None for anything else, which the model reads: any
    other word, a question mark, a pause, a letter past the `count` options."""
    text = " ".join(said.lower().replace("’", "'").replace(":", " ").split())
    text = END.sub("", text)

    if not text or NOT_PLAIN.search(text):
        return None

    joins = "|".join(sorted(AND_WORDS.get(language, ())))
    # Commas, or a word for "and" (after a comma or not: "A, B, and D").
    between = rf"\s*,?\s+(?:{joins})\s+|\s*,\s*" if joins else r"\s*,\s*"
    words = LETTER_WORDS.get(language, frozenset())
    items = re.split(between, text)
    picks = [letter_of(item, words, count) for item in items]

    if any(pick is None for pick in picks):
        return None

    return sorted({pick for pick in picks if pick is not None})
