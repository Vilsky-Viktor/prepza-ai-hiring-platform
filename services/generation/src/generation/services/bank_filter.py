"""The shared question bank's filter: before a company's question joins the bank that other
companies' interviews reuse from, it must name and reveal nothing about an organisation or a
person (docs/generation.md, The question bank). Library offers the questions and keeps the
verdicts; this service only judges them."""

import asyncio
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from testee_common.limits import pause
from testee_common.redis import redis_lock

from generation.constants.actions import BANK_FILTER
from generation.constants.bank import (
    BANK_FILTER_AT_ONCE,
    BANK_FILTER_LOCK_KEY,
    BANK_FILTER_LOCK_SECONDS,
    BANK_FILTER_PAGE,
    MAX_BANK_CHECKS,
)
from generation.helpers.bank_filter import bank_text, has_contact_details
from generation.integrations import library, llm
from generation.integrations.redis import get_redis
from generation.integrations.usage import ai_run
from generation.prompts.bank_filter import BANK_FILTER_INPUT, BANK_FILTER_SYSTEM
from generation.schemas.bank_filter import BankCandidate, BankCheck, BankVerdict

logger = logging.getLogger(__name__)


async def is_general(topic: str, text: str, options: list[str]) -> bool:
    """Whether anyone could have written the question for any employer: no contact details
    (checked by code), and nothing the model finds naming or revealing an organisation or a
    private person. Raises when the model's call fails."""
    question = bank_text(topic, text, options)

    if has_contact_details(question):
        return False

    messages = [
        SystemMessage(content=BANK_FILTER_SYSTEM),
        HumanMessage(content=BANK_FILTER_INPUT.format(question=question)),
    ]
    verdict: BankVerdict = (
        await llm.get_bank_filter_llm().with_structured_output(BankVerdict).ainvoke(messages)
    )

    return not verdict.identifies


async def check_page(candidates: list[BankCandidate]) -> list[BankCheck]:
    """Each candidate's verdict, a few at once; one whose call failed has none and is offered
    again on the next run."""
    limit = asyncio.Semaphore(BANK_FILTER_AT_ONCE)

    async def check(candidate: BankCandidate) -> BankCheck | None:
        async with limit:
            try:
                passed = await is_general(candidate.topic, candidate.text, candidate.options)
            except Exception:
                logger.exception("Couldn't check question %s for the bank", candidate.question_id)

                return None

        return BankCheck(question_id=candidate.question_id, text=candidate.text, passed=passed)

    checks = await asyncio.gather(*(check(candidate) for candidate in candidates))

    return [found for found in checks if found is not None]


async def check_all() -> int:
    """Every question library offers, a page at a time in id order, up to MAX_BANK_CHECKS; each
    page's verdicts are saved before the next page is read. How many were checked."""
    checked = 0
    after = None

    async with ai_run(BANK_FILTER):
        while checked < MAX_BANK_CHECKS:
            page = await library.bank_candidates(BANK_FILTER_PAGE, after)

            if not page:
                break

            checks = await check_page(page)

            if checks:
                await library.save_bank_checks(checks)

            checked += len(checks)
            after = page[-1].question_id

    return checked


async def run() -> None:
    """Daily: companies' questions checked for the bank. One run at a time, none during the
    emergency pause (it's AI)."""
    redis = get_redis()

    if await pause.is_paused(redis):
        logger.warning("The bank filter skipped: the emergency pause is on")

        return

    token = await redis_lock.acquire(redis, BANK_FILTER_LOCK_KEY, BANK_FILTER_LOCK_SECONDS)

    if token is None:
        logger.warning("The bank filter is still running from the last time; skipped")

        return

    try:
        logger.info("The bank filter checked %d questions", await check_all())
    finally:
        await redis_lock.release(redis, BANK_FILTER_LOCK_KEY, token)
