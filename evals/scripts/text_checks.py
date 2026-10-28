"""Checks by code on text a model wrote in a given language, shared by the translation, title and
voice tests: whether it's written in that language's script, what it must keep as it is, and how
far it is from the text it should match."""

import re
import unicodedata

# The letters each language is written in; Latin for the rest.
SCRIPTS = {
    "ja": r"[぀-ヿ一-鿿]",
    "zh": r"[一-鿿]",
    "ko": r"[가-힯]",
    "ar": r"[؀-ۿ]",
    "fa": r"[؀-ۿ]",
    "he": r"[֐-׿]",
    "th": r"[฀-๿]",
    "hi": r"[ऀ-ॿ]",
    "ru": r"[Ѐ-ӿ]",
    "uk": r"[Ѐ-ӿ]",
}
LATIN = r"[A-Za-zÀ-ɏ]"
URL = re.compile(r"https?://\S+")
# At least this share of a text's letters (names and links aside) is in its language's script.
MIN_SCRIPT_SHARE = 0.6


def in_script(text: str, language: str, keep: list[str] = ()) -> bool:
    """Most of the text's letters, names in `keep` and links aside, are in the language's
    script. Latin-script languages only need any letters at all."""
    text = URL.sub("", text)

    for name in keep:
        text = text.replace(name, "")

    letters = re.findall(r"\w", text)
    letters = [letter for letter in letters if not letter.isdigit() and letter != "_"]

    if not letters:
        return False

    pattern = SCRIPTS.get(language, LATIN)
    found = sum(bool(re.match(pattern, letter)) for letter in letters)

    return found / len(letters) >= MIN_SCRIPT_SHARE


def keeps(text: str, names: list[str]) -> bool:
    """Every name appears in the text exactly as written."""
    return all(name in text for name in names)


def paragraphs(text: str) -> int:
    return len([part for part in re.split(r"\n\s*\n", text.strip()) if part.strip()])


def plain(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower()

    return re.sub(r"[^\w]+", "", text)


def error_rate(said: str, heard: str) -> float:
    """Levenshtein distance between the two, case, spaces and punctuation aside, over the
    length of what was said."""
    a, b = plain(said), plain(heard)
    row = list(range(len(b) + 1))

    for i, x in enumerate(a, 1):
        previous, row[0] = row[0], i

        for j, y in enumerate(b, 1):
            previous, row[j] = row[j], min(row[j] + 1, row[j - 1] + 1, previous + (x != y))

    return row[-1] / max(len(a), 1)
