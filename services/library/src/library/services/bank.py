"""The shared question bank: companies' proven questions that passed generation's filter join
it; an interview kept private, a flag or a report takes them out. Deleting a company, an
interview or an account never deletes a bank copy (models/bank.py)."""

import logging
import uuid

from testee_common.events.interviews import InterviewPrivacyChanged

from library.constants.bank import BANK_SWEEP_BATCH
from library.core.db import Session
from library.repositories import bank
from library.schemas.bank import BankCandidate, BankCheckIn

logger = logging.getLogger(__name__)


async def candidates(limit: int, after: uuid.UUID | None) -> list[BankCandidate]:
    async with Session() as session:
        found = await bank.candidates(session, limit, after)

    return [
        BankCandidate(
            question_id=question_id,
            topic=topic,
            text=wording,
            options=[option["answer"] for option in options],
        )
        for question_id, topic, wording, options in found
    ]


async def save_checks(checks: list[BankCheckIn]) -> None:
    """The verdicts, and the proven questions that passed joining the bank, in one save; a
    repeat changes nothing."""
    async with Session.begin() as session:
        await bank.save_checks(session, [(c.question_id, c.text, c.passed) for c in checks])
        await bank.join(session, [check.question_id for check in checks if check.passed])


async def privacy_changed(data: dict) -> None:
    """interview.privacy_changed: kept private, the interview's questions leave the bank (copies
    reused elsewhere stay); let back in, those that may join do. An older change than the one
    saved changes nothing, so a redelivery or an out-of-order event is harmless."""
    event = InterviewPrivacyChanged.model_validate(data)
    where = (event.company_id, event.set_id, event.generation_id)

    async with Session.begin() as session:
        saved = await bank.set_privacy(
            session, event.interview_id, *where, event.keep_private, event.changed_at
        )

        if not saved:
            return

        if event.keep_private:
            await bank.leave_set(session, *where)
        else:
            await bank.join_set(session, *where)


async def sweep() -> int:
    """Daily: bank copies a flag, a report or an opt-out should have taken out but that joined
    in a transaction racing it. A flag or report bars the source for good. How many left."""
    async with Session.begin() as session:
        found = await bank.stale(session, BANK_SWEEP_BATCH)
        await bank.remove(session, [bank_id for bank_id, _, _ in found])
        await bank.bar(session, [source for _, source, private in found if not private])

    return len(found)
