import re

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from prepza_common.config.constants import LANGUAGES

from rounds.constants.voice import LETTERS, Intent
from rounds.constants.voice_confirmations import CONFIRMATIONS
from rounds.helpers.voice_letters import plain_letters
from rounds.helpers.voice_speech import read_aloud
from rounds.prompts.voice_match import MULTI, NOTHING_WAITING, SINGLE, SYSTEM, USER
from rounds.schemas.rounds import NextQuestion
from rounds.schemas.voice import VoiceMatch

# Where speech recognition breaks a reply into parts ("Yeah, that's right.").
PART_BREAKS = re.compile(r"[,.!?;:¡¿…]+")
# How speech recognition writes a sound that isn't words: "[cough]", "(laughs)", "*sigh*".
SOUND_TAGS = re.compile(r"\[[^\]]*\]|\([^)]*\)|\*[^*]*\*|<[^>]*>")
WORD = re.compile(r"\w")


def is_noise(said: str) -> bool:
    """Nothing heard but sounds: an empty transcript, or only sound tags, punctuation or
    symbols ("[cough]", "...", "♪"), in any script."""
    return WORD.search(SOUND_TAGS.sub("", said)) is None


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


def hearing_keywords(question: NextQuestion) -> list[str]:
    """What speech recognition is told it's likely to hear: the options' letters and the texts of
    those read aloud."""
    letters = list(LETTERS[: len(question.options)])

    return letters + [option.strip() for option in question.options if read_aloud(option)]


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


def obvious(
    said: str, question: NextQuestion, waiting: list[int], language: str
) -> tuple[Intent, list[int]] | None:
    """A reply plain enough to understand without the model: only a yes (CONFIRMATIONS, each
    part) while a choice is waiting, or only options' letters (helpers/voice_letters.py: "B.",
    "option B", several on a select-all-that-apply question), a new choice even while one
    waits. None for anything else, which the model reads."""
    parts = [" ".join(part.split()) for part in PART_BREAKS.split(said.lower().replace("’", "'"))]
    parts = [part for part in parts if part]
    yes = CONFIRMATIONS.get(language, frozenset())

    if waiting and parts and all(part in yes for part in parts):
        return Intent.CONFIRM, sorted(waiting)

    picks = plain_letters(said, len(question.options), language)

    if picks and (question.multi or len(picks) == 1):
        return Intent.CHOOSE, picks

    return None
