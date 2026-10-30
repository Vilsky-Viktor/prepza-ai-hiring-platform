from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from prepza_common.config.constants import LANGUAGES

from rounds.constants.voice import LETTERS, Intent
from rounds.prompts.voice_match import MULTI, NOTHING_WAITING, SINGLE, SYSTEM, USER
from rounds.schemas.rounds import NextQuestion
from rounds.schemas.voice import VoiceMatch


def letters_of(picks: list[int]) -> str:
    """Options' indices as their letters: "A, C"."""
    return ", ".join(LETTERS[pick] for pick in sorted(picks))


def match_prompt(
    question: NextQuestion, said: str, waiting: list[int], language: str
) -> list[BaseMessage]:
    """The matching call's messages: the fixed instructions, then the question, its options
    (never which are right: NextQuestion has no answer key), the choice waiting for
    confirmation and what the candidate said, tagged as data."""
    options = "\n".join(
        f"{LETTERS[index]}. {option}" for index, option in enumerate(question.options)
    )
    user = USER.format(
        language=LANGUAGES.get(language, language),
        question=question.text,
        options=options,
        kind=MULTI if question.multi else SINGLE,
        waiting=letters_of(waiting) if waiting else NOTHING_WAITING,
        said=said,
    )

    return [SystemMessage(content=SYSTEM), HumanMessage(content=user)]


def understood(match: VoiceMatch, multi: bool, waiting: list[int]) -> tuple[Intent, list[int]]:
    """What the code accepts of the model's reading, and the options it picks: a choice of
    options that exist (one for a single-answer question); a confirmation or a no only while a
    choice is waiting, a confirmation picking that choice. Anything else is unclear."""
    unclear = (Intent.UNCLEAR, [])

    if match.intent == Intent.CHOOSE:
        picks = sorted({LETTERS.index(letter) for letter in match.letters})

        if not picks or (not multi and len(picks) != 1):
            return unclear

        return Intent.CHOOSE, picks

    if match.intent in (Intent.CONFIRM, Intent.REJECT) and waiting:
        return match.intent, sorted(waiting) if match.intent == Intent.CONFIRM else []

    return unclear
