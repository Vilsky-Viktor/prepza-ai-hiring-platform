"""An action recorded on its own, after a change saved elsewhere (billing, generation, library):
the other service's call can't share a transaction with the log."""

from companies.core.db import Session
from companies.repositories import audit


async def record(company_id, user_id: str, action: str, target_id=None, **details) -> None:
    async with Session.begin() as session:
        await audit.record(session, company_id, user_id, action, target_id, **details)


async def record_interview(interview, user_id: str, action: str, via: str | None = None) -> None:
    async with Session.begin() as session:
        await audit.record_interview(session, interview, user_id, action, via)
