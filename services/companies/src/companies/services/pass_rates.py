"""Pass rates per company interview for the superadmin's monitoring
(internal_docs/compliance/post-market-monitoring-plan.md)."""

from uuid import UUID

from companies.core.db import Session
from companies.helpers.pass_rates import outside_triggers, percent
from companies.integrations import rounds
from companies.repositories import pass_rates
from companies.schemas.monitoring import PassRateOut


async def page(by_finished: bool, after: UUID | None, limit: int) -> list[PassRateOut]:
    """A page after the interview `after` (the last one shown), with each test's share of
    answers that ran out of time from rounds."""
    async with Session() as session:
        rows = await pass_rates.page(session, by_finished, after, limit)

    answers = await rounds.answer_counts([row.set_id for row in rows if row.set_id])

    return [
        PassRateOut(
            interview_id=row.id,
            title=row.title,
            company=row.company,
            finished=row.finished,
            pass_rate=percent(row.passed, row.finished),
            pass_mark=row.pass_mark,
            average_grade=round(row.average),
            timeout_share=percent(*answers.get(str(row.set_id), (0, 0))),
            outside_triggers=outside_triggers(row.passed, row.finished),
        )
        for row in rows
    ]
