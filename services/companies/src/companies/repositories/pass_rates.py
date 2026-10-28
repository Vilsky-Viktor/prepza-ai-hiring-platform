"""Pass rates per company interview for the superadmin's monitoring (internal_docs/compliance/
post-market-monitoring-plan.md): read from each interview's counters (interview_results, kept by
triggers as invites finish), sorted and paged by key in SQL."""

import uuid

from sqlalchemy import Float, Row, cast, literal, select, tuple_

from companies.core.db import Session
from companies.models.companies import Company
from companies.models.interview_results import InterviewResult
from companies.models.interviews import Interview


def sort_key(by_finished: bool) -> tuple:
    """The list's order as one ascending tuple: most finished first, or lowest pass rate first
    (then most finished); the interview's id breaks ties."""
    finished = InterviewResult.finished

    if by_finished:
        return (-finished, InterviewResult.interview_id)

    return (cast(InterviewResult.passed, Float) / finished, -finished, InterviewResult.interview_id)


async def page(by_finished: bool, after: uuid.UUID | None, limit: int) -> list[Row]:
    """Interviews with finished candidates, `limit` after the interview `after` (the last one
    shown). Each row has the interview's id, title, set_id, pass_mark, the company's name, and
    the finished, passed and average (grade) of its candidates."""
    key = sort_key(by_finished)
    query = (
        select(
            Interview.id,
            Interview.title,
            Interview.set_id,
            Interview.pass_mark,
            Company.name.label("company"),
            InterviewResult.finished,
            InterviewResult.passed,
            (cast(InterviewResult.grade_total, Float) / InterviewResult.finished).label("average"),
        )
        .join(Interview, Interview.id == InterviewResult.interview_id)
        .join(Company, Company.id == Interview.company_id)
        .where(InterviewResult.finished > 0)
        .order_by(*key)
        .limit(limit)
    )

    if after is not None:
        # The last row's own place in that order: the rows after it.
        mine = InterviewResult.interview_id == after
        place = [select(column).where(mine).scalar_subquery() for column in key[:-1]]
        query = query.where(tuple_(*key) > tuple_(*place, literal(after)))

    async with Session() as session:
        return list(await session.execute(query))
