import re

from app.constants.patterns import DENIED_TERMS, QUOTED_WORDS
from app.schemas.patterns import QualitySignal


def words(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def normalized(text: str) -> str:
    """The text's words only, lowercase: two wordings that differ only in case or punctuation
    match."""
    return " ".join(words(text))


def option_lines(options, picks: dict[str, int], answers: int) -> list[str]:
    lines = []

    for option in options:
        mark = "[correct] " if option.correct else ""
        line = f"- {mark}{option.answer}"

        if answers:
            line += f" (picked by {round(100 * picks.get(option.answer, 0) / answers)}%)"

        lines.append(line)

    return lines


def question_block(number: int, signal: QualitySignal) -> str:
    """One question as the pattern prompt shows it: numbered, without any id or set."""
    lines = [
        f"{number}. {signal.text}",
        *option_lines(signal.options, signal.option_picks, signal.answers),
    ]

    if signal.answers:
        right = round(100 * signal.correct / signal.answers)
        lines.append(f"Answered {signal.answers} times, {right}% right.")

    if signal.timeouts:
        lines.append(f"Time ran out {signal.timeouts} times.")

    if signal.reasons:
        reported = ", ".join(f"{reason}: {count}" for reason, count in signal.reasons.items())
        lines.append(f"Reports: {reported}.")

    if signal.dislikes:
        lines.append(f"Thumbs up {signal.likes}, thumbs down {signal.dislikes}.")

    if signal.new_text:
        lines.append(f"Replaced by: {signal.new_text}")
        lines += option_lines(signal.new_options or [], {}, 0)

    return "\n".join(lines)


def known_block(texts: list[str]) -> str:
    return "\n".join(f"{number}. {text}" for number, text in enumerate(texts, 1)) or "None"


def names_something(text: str) -> str | None:
    """Why a pattern isn't general, or None: it has a word that names a technology, field or
    role (DENIED_TERMS), or a capitalized word that doesn't start a sentence, most likely a
    name."""
    lowered = text.lower()

    for term in DENIED_TERMS:
        if re.search(rf"\b{term}", lowered):
            return f"names '{term}'"

    sentences = re.split(r"[.!?:]\s+", text)
    capitalized = [
        word
        for sentence in sentences
        for word in re.findall(r"\w+", sentence)[1:]
        if word[0].isupper()
    ]

    if capitalized:
        return "has a capitalized word"

    return None


def shingles(text: str) -> set[tuple[str, ...]]:
    found = words(text)

    return {tuple(found[i : i + QUOTED_WORDS]) for i in range(len(found) - QUOTED_WORDS + 1)}


def signal_texts(signal: QualitySignal) -> list[str]:
    options = [*signal.options, *(signal.new_options or [])]

    return [signal.text, signal.new_text or "", *(option.answer for option in options)]


def quotes_input(text: str, signals: list[QualitySignal]) -> bool:
    """The pattern shares QUOTED_WORDS words in a row with a question, its options or its
    replacement."""
    own = shingles(text)

    return any(own & shingles(part) for signal in signals for part in signal_texts(signal))
