"""Every AI call and limit hit the services record, kept once each by its event id, and dropped
once past their retention."""

from datetime import datetime

from prepza_common.ai.ai_constants import Category

from billing.constants.usage import CHANGES_KEEP_DAYS, USAGE_KEEP_DAYS
from billing.core.db import Session
from billing.helpers.usage import category_of
from billing.repositories import usage


async def record_usage(event_id: str, occurred_at: datetime, data: dict) -> Category | None:
    """Stores one AI call, deciding who it was for: a company that had topped up by the call's
    time is paid. None when the event was stored before."""
    company_id = data.get("company_id")

    async with Session.begin() as session:
        paid = company_id is not None and await usage.company_paid(session, company_id, occurred_at)
        category = category_of(data.get("action"), company_id, bool(paid))
        stored = await usage.store_usage(session, event_id, occurred_at, data, category)

    return category if stored else None


async def record_hit(event_id: str, occurred_at: datetime, data: dict) -> None:
    async with Session.begin() as session:
        await usage.store_hit(session, event_id, occurred_at, data)


async def drop_old(now: datetime) -> None:
    """AI usage and limit hits past USAGE_KEEP_DAYS, limit changes past CHANGES_KEEP_DAYS, a
    batch at a time."""
    await usage.drop_old(Session, now, USAGE_KEEP_DAYS, CHANGES_KEEP_DAYS)
