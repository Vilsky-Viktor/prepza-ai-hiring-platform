import logging
from uuid import UUID

from fastapi import HTTPException, status
from langchain_core.messages import HumanMessage, SystemMessage
from prepza_common.limits import pause
from prepza_common.redis import redis_lock

from generation.constants.actions import QUALITY_PATTERNS
from generation.constants.patterns import (
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
from generation.core.db import Session
from generation.helpers.patterns import (
    known_block,
    names_something,
    normalized,
    question_block,
    quotes_input,
)
from generation.integrations import library, llm
from generation.integrations.redis import get_redis
from generation.integrations.usage import ai_run
from generation.models.patterns import QualityPattern
from generation.prompts.patterns import FLAG_MEANINGS, PATTERNS_INPUT, PATTERNS_SYSTEM
from generation.repositories import patterns
from generation.schemas.patterns import ProposedPattern, ProposedPatterns, QualitySignal

logger = logging.getLogger(__name__)


def rejection(pattern: ProposedPattern, signals: list[QualitySignal]) -> str | None:
    """Why a new pattern isn't kept, or None: too long, naming something, or quoting a question."""
    if len(pattern.text) > MAX_PATTERN_CHARS:
        return "too long"

    if quotes_input(pattern.text, signals):
        return "quotes a question"

    return names_something(pattern.text)


async def find_patterns(
    flag: str, signals: list[QualitySignal], known: list[str]
) -> ProposedPatterns:
    """The model's recurring mistakes in one flag's questions, `known` being the patterns it
    may name by number instead."""
    system = PATTERNS_SYSTEM.format(
        min_questions=MIN_PATTERN_QUESTIONS, max_chars=MAX_PATTERN_CHARS
    )
    request = PATTERNS_INPUT.format(
        meaning=FLAG_MEANINGS.get(flag, ""),
        known=known_block(known),
        questions="\n\n".join(
            question_block(number, signal) for number, signal in enumerate(signals, 1)
        ),
    )

    return (
        await llm.get_patterns_llm()
        .with_structured_output(ProposedPatterns)
        .ainvoke([SystemMessage(content=system), HumanMessage(content=request)])
    )


async def propose(flag: str, signals: list[QualitySignal]) -> None:
    """Asks the model for the recurring mistakes in one flag's questions; a new one is stored as
    proposed, a known one counts again (a dismissed one stays dismissed). What the model found
    is saved in one transaction, after its call: all of it or, on a failure, none."""
    async with Session() as session:
        known = await patterns.for_flag(session, flag)

    async with ai_run(QUALITY_PATTERNS):
        result = await find_patterns(flag, signals, [pattern.text for pattern in known])

    seen, new = sorted_out(flag, signals, known, result)

    async with Session.begin() as session:
        for pattern_id, count in seen:
            await patterns.seen(session, pattern_id, count)

        for text, count in new:
            await patterns.add(session, text, flag, count)

    for _, count in new:
        logger.info("Pattern for %s proposed, shown by %d questions", flag, count)


def sorted_out(
    flag: str,
    signals: list[QualitySignal],
    known: list[QualityPattern],
    result: ProposedPatterns,
) -> tuple[list[tuple[UUID, int]], list[tuple[str, int]]]:
    """The model's patterns sorted out: the known ones it found again, as (id, questions), and
    the new ones to keep, as (text, questions). Too few questions, a dismissed pattern and a
    rejected text are left out."""
    seen = []
    new = []

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
                seen.append((same[0].id, count))

            logger.info("Pattern %s for %s seen again in %d questions", same[0].id, flag, count)

            continue

        reason = rejection(proposed, signals)

        if reason is not None:
            # Not its text: a rejected pattern may quote a company's question.
            logger.warning("Pattern for %s rejected: %s", flag, reason)

            continue

        new.append((proposed.text, count))

    return seen, new


async def review(pattern_id: UUID, decision: PatternStatus, superadmin_id: str) -> None:
    """A superadmin approves or dismisses a proposed pattern; only one review wins."""
    async with Session.begin() as session:
        reviewed = await patterns.review(session, pattern_id, decision, superadmin_id)

    if not reviewed:
        raise HTTPException(status.HTTP_409_CONFLICT, "This pattern was already reviewed")

    logger.info("Quality pattern %s %s by superadmin %s", pattern_id, decision, superadmin_id)


async def run() -> None:
    """Weekly: the questions flagged or replaced in the last week, by flag, turned into proposed
    general rules for a superadmin to review. One run at a time, none during the emergency
    pause (it's AI), and each flag once a week."""
    redis = get_redis()

    if await pause.is_paused(redis):
        logger.warning("Quality patterns skipped: the emergency pause is on")

        return

    token = await redis_lock.acquire(redis, PATTERN_LOCK_KEY, PATTERN_LOCK_SECONDS)

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
        await redis_lock.release(redis, PATTERN_LOCK_KEY, token)
