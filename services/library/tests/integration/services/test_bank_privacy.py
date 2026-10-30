"""Companies' opt-out from the shared question bank (`keep_private`, companies'
interview.privacy_changed), and which companies' flagged questions the evals may keep."""

import uuid
from datetime import timedelta

from sqlalchemy import text

from library.constants.quality import QualityFlag
from library.core.db import Session
from library.repositories import preparations, quality, quality_signals
from library.services import bank as bank_service
from tests.integration.bank_factories import (
    NOW,
    bank_rows,
    check,
    privacy,
    prove,
    reused_interview,
    shared_interview,
)
from tests.integration.factories import a_company, direction, interview, question_ids
from tests.integration.handlers.test_deletion_events import pushed
from tests.integration.transactions import transaction


async def candidate_ids() -> set:
    return {c.question_id for c in await bank_service.candidates(100, None)}


def test_keeping_an_interview_private_takes_its_questions_out_until_let_back_in(run):
    """Copies reused elsewhere stay; an older or repeated change changes nothing."""
    company, other = a_company(str(uuid.uuid4())), a_company(str(uuid.uuid4()))
    interview_id = uuid.uuid4()

    async def scenario():
        set_id, ids = await shared_interview(company, questions=2)
        bank = await bank_rows(ids)
        new = await reused_interview(other, [bank[ids[0]]])
        on = privacy(company, set_id, True, NOW, interview_id)
        stale_off = privacy(company, set_id, False, NOW - timedelta(minutes=1), interview_id)
        codes = await pushed("interview.privacy_changed", on)
        codes += await pushed("interview.privacy_changed", stale_off)
        private = await bank_rows(ids), await candidate_ids(), await question_ids(new)
        off = privacy(company, set_id, False, NOW + timedelta(minutes=1), interview_id)
        codes += await pushed("interview.privacy_changed", off)

        return codes, ids, private, await bank_rows(ids)

    codes, ids, (private, offered_now, copies), back = run(scenario())

    assert codes == [204] * 6
    assert private == {}
    assert not set(ids) & offered_now
    assert len(copies) == 1
    assert set(back) == set(ids)


def test_an_opt_out_before_the_questions_are_saved_holds_by_the_generation(run):
    """Kept private while it was generating: the set is found by its generation."""
    company = a_company(str(uuid.uuid4()))

    async def scenario():
        set_id = await interview(
            f"Early {uuid.uuid4()}", owner=company, questions=1, embedding=direction(1.0)
        )
        generation_id = (await transaction(preparations.get, set_id)).generation_id

        async with Session.begin() as session:
            await session.execute(
                text("UPDATE sets SET generation_id = :g WHERE id = :id"),
                {"g": generation_id, "id": set_id},
            )

        await pushed(
            "interview.privacy_changed",
            privacy(company, None, True, generation_id=generation_id),
        )
        ids = await question_ids(set_id)
        await prove(ids)

        return ids, await candidate_ids()

    ids, offered_now = run(scenario())

    assert not set(ids) & offered_now


def test_only_filtered_companies_flagged_questions_reach_the_evals(run):
    """export_flagged.py's company_questions(): flagged, passed the filter, not kept private."""
    company = a_company(str(uuid.uuid4()))

    async def scenario():
        set_id = await interview(f"Evals {uuid.uuid4()}", owner=company, questions=3)
        cleared, refused, private = await question_ids(set_id)
        # Passed but never flagged: not a trap.
        await check([private])
        hidden = await interview(f"Hidden {uuid.uuid4()}", owner=company, questions=1)
        [kept_out] = await question_ids(hidden)
        await check([cleared, kept_out])
        await check([refused], passed=False)

        for question_id in (cleared, refused, kept_out):
            await transaction(quality.save_flag, question_id, QualityFlag.REWRITE)

        await pushed("interview.privacy_changed", privacy(company, hidden, True))
        found = await transaction(quality_signals.flagged_companies)

        return (cleared, refused, private, kept_out), {question.id for question, *_ in found}

    (cleared, refused, unflagged, kept_out), found = run(scenario())

    assert cleared in found
    assert not {refused, unflagged, kept_out} & found
