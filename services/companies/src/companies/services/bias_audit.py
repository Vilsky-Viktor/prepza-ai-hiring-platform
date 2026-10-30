"""The owner's bias-audit export: every candidate who finished with a grade, as CSV rows the
company joins with its own self-reported categories for its independent auditor
(constants/bias_audit.py)."""

import asyncio
from datetime import datetime

from fastapi import HTTPException, status
from prepza_common.events.audit_actions import AuditAction, TargetKind
from prepza_common.limits.rate_limit import hit_or_skip

from companies.constants.reports import READ_BATCH
from companies.core.db import Session
from companies.helpers.bias_audit import audit_csv
from companies.integrations.redis import get_redis
from companies.models.companies import Company
from companies.repositories import audit
from companies.repositories import bias_audit as outcomes
from companies.repositories import interviews
from companies.services.candidate_results import store_missing


async def chosen_interview(company: Company, interview_id):
    """The interview asked for, when one is: only one of the company's own."""
    if interview_id is None:
        return None

    async with Session() as session:
        interview = await interviews.get(session, interview_id)

    if interview is None or interview.company_id != company.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Interview not found")

    return interview


async def read_all(filters: list) -> list:
    """Every (invite, interview) pair in the scope, a batch at a time."""
    rows: list = []

    while True:
        async with Session() as session:
            batch = await outcomes.outcomes(session, filters, len(rows), READ_BATCH)

        rows += batch

        if len(batch) < READ_BATCH:
            return rows


async def record(company: Company, user_id: str, interview) -> None:
    """The export in the action log: what it covered, the interview or the whole company."""
    async with Session.begin() as session:
        if interview is not None:
            await audit.record_interview(
                session, interview, user_id, AuditAction.BIAS_AUDIT_EXPORTED
            )

            return

        await audit.record(
            session,
            company.id,
            user_id,
            AuditAction.BIAS_AUDIT_EXPORTED,
            company.id,
            target_kind=TargetKind.COMPANY,
            target_label=company.name,
        )


async def export(
    company: Company,
    user_id: str,
    interview_id=None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> str:
    """The CSV of the company's (or one interview's) candidates who finished with a grade, from
    `start` and before `end` when given; counted against the company's daily exports and
    recorded in its action log."""
    interview = await chosen_interview(company, interview_id)
    who = {"company_id": company.id, "user_id": user_id}
    key = f"rate:bias-audit:{company.id}"
    await hit_or_skip(get_redis(), key, "BIAS_AUDIT_EXPORTS_PER_DAY", **who)
    filters = outcomes.scope(company.id, interview_id, start, end)

    async with Session() as session:
        missing = await outcomes.unscored(session, filters)

    await store_missing(missing)
    text = await asyncio.to_thread(audit_csv, await read_all(filters))
    await record(company, user_id, interview)

    return text
