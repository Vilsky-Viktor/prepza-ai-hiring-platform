import logging

from langchain_core.messages import HumanMessage
from prepza_common import pause

from app.constants.actions import QUALITY_PATTERNS
from app.constants.patterns import (
    MAX_PATTERN_CHARS,
    MAX_PATTERN_QUESTIONS,
    MIN_PATTERN_QUESTIONS,
    PATTERN_DONE_KEY,
    PATTERN_DONE_SECONDS,
    PATTERN_LOCK_KEY,
    PATTERN_LOCK_SECONDS,
    PATTERN_WINDOW_DAYS,
    PatternStatus,
)
from app.helpers.patterns import (
    known_block,
    names_something,
    normalized,
    question_block,
    quotes_input,
)
from app.integrations import library, llm
from app.integrations.redis import get_redis
from app.integrations.usage import ai_run
from app.prompts.patterns import FLAG_MEANINGS, PATTERNS_PROMPT
from app.schemas.patterns import ProposedPattern, ProposedPatterns, QualitySignal
from app.storage import locks, patterns

logger = logging.getLogger(__name__)


def rejection(pattern: ProposedPattern, signals: list[QualitySignal]) -> str | None:
    """Why a new pattern isn't kept, or None: too long, naming something, or quoting a question."""
    if len(pattern.text) > MAX_PATTERN_CHARS:
        return "too long"

    if quotes_input(pattern.text, signals):
        return "quotes a question"

    return names_something(pattern.text)


async def propose(flag: str, signals: list[QualitySignal]) -> None:
    """Asks the model for the recurring mistakes in one flag's questions; a new one is stored as
    proposed, a known one counts again (a dismissed one stays dismissed)."""
    known = await patterns.for_flag(flag)
    prompt = PATTERNS_PROMPT.format(
        meaning=FLAG_MEANINGS.get(flag, ""),
        min_questions=MIN_PATTERN_QUESTIONS,
        max_chars=MAX_PATTERN_CHARS,
        known=known_block([pattern.text for pattern in known]),
        questions="\n\n".join(
            question_block(number, signal) for number, signal in enumerate(signals, 1)
        ),
    )

    async with ai_run(QUALITY_PATTERNS):
        result: ProposedPatterns = (
            await llm.get_verifier_llm()
            .with_structured_output(ProposedPatterns)
            .ainvoke([HumanMessage(content=prompt)])
        )

    for proposed in result.patterns:
        proposed.text = proposed.text.strip()
        count = len({number for number in proposed.questions if 1 <= number <= len(signals)})

        if count < MIN_PATTERN_QUESTIONS:
            logger.info("Pattern for %s left out: shown by %d questions", flag, count)

            continue

        same = [
            pattern
            for number, pattern in enumerate(known, 1)
            if number == proposed.same_as or normalized(pattern.text) == normalized(proposed.text)
        ]

        if same:
            if same[0].status != PatternStatus.DISMISSED:
                await patterns.seen(same[0].id, count)

            logger.info("Pattern %s for %s seen again in %d questions", same[0].id, flag, count)

            continue

        reason = rejection(proposed, signals)

        if reason is not None:
            # Not its text: a rejected pattern may quote a company's question.
            logger.warning("Pattern for %s rejected: %s", flag, reason)

            continue

        await patterns.add(proposed.text, flag, count)
        logger.info("Pattern for %s proposed, shown by %d questions", flag, count)


async def run() -> None:
    """Weekly: the questions flagged or replaced in the last week, by flag, turned into proposed
    general rules for a superadmin to review. One run at a time, none during the emergency
    pause (it's AI), and each flag once a week."""
    redis = get_redis()

    if await pause.is_paused(redis):
        logger.warning("Quality patterns skipped: the emergency pause is on")

        return

    token = await locks.acquire(redis, PATTERN_LOCK_KEY, PATTERN_LOCK_SECONDS)

    if token is None:
        logger.warning("Quality patterns are still running from the last time; skipped")

        return

    try:
        by_flag: dict[str, list[QualitySignal]] = {}

        for signal in await library.quality_signals(PATTERN_WINDOW_DAYS):
            by_flag.setdefault(signal.flag, []).append(signal)

        for flag, signals in by_flag.items():
            done = PATTERN_DONE_KEY.format(flag=flag)

            if len(signals) < MIN_PATTERN_QUESTIONS or await redis.exists(done):
                continue

            await propose(flag, signals[:MAX_PATTERN_QUESTIONS])
            await redis.set(done, 1, ex=PATTERN_DONE_SECONDS)
    finally:
        await locks.release(redis, PATTERN_LOCK_KEY, token)
