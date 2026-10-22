"""Every AI call and limit hit the services record, stored once each (by event id)."""

from datetime import datetime, timedelta
from decimal import Decimal

from prepza_common.ai_constants import PREPZA_ACTIONS, Category
from prepza_common.db import delete_in_batches, update_in_batches
from sqlalchemy import exists, select
from sqlalchemy.dialects.postgresql import insert

from app.constants.products import OwnerType
from app.models.billing import Purchase
from app.models.limits import LimitChange
from app.models.usage import AiUsage, LimitHit
from app.storage.db import Session

USAGE_FIELDS = (
    "action",
    "service",
    "model",
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "audio_seconds",
    "company_id",
    "user_id",
    "subject_id",
    "outcome",
)
HIT_FIELDS = ("limit", "kind", "scope", "company_id", "user_id", "what")


def category_of(action: str, company_id: str | None, paid: bool) -> Category:
    if company_id:
        return Category.PAID if paid else Category.UNPAID

    return Category.PREPZA if action in PREPZA_ACTIONS else Category.NO_COMPANY


async def store_usage(event_id: str, occurred_at: datetime, data: dict) -> Category | None:
    """Stores one AI call, deciding who it was for: a company that had topped up by the call's
    time is paid. None when the event was stored before."""
    values = {field: data.get(field) for field in USAGE_FIELDS}
    # The event's float cost, exactly: its shortest decimal form.
    values["cost"] = Decimal(str(data.get("cost_usd") or 0))
    company_id = values["company_id"]

    async with Session() as session:
        paid = company_id is not None and await session.scalar(
            select(
                exists().where(
                    Purchase.owner_type == OwnerType.COMPANY,
                    Purchase.owner_id == company_id,
                    Purchase.created_at <= occurred_at,
                )
            )
        )
        category = category_of(values["action"], company_id, bool(paid))
        stored = await session.scalar(
            insert(AiUsage)
            .values(event_id=event_id, occurred_at=occurred_at, category=category, **values)
            .on_conflict_do_nothing(index_elements=["event_id"])
            .returning(AiUsage.id)
        )
        await session.commit()

    return category if stored is not None else None


async def store_hit(event_id: str, occurred_at: datetime, data: dict) -> None:
    values = {field: data.get(field) for field in HIT_FIELDS}

    async with Session() as session:
        await session.execute(
            insert(LimitHit)
            .values(event_id=event_id, occurred_at=occurred_at, **values)
            .on_conflict_do_nothing(index_elements=["event_id"])
        )
        await session.commit()


async def forget(column: str, value: str) -> None:
    """Empties a deleted account's or company's id in both tables, a batch at a time, each
    batch its own transaction; the costs and hits stay."""
    for model in (AiUsage, LimitHit):
        field = getattr(model, column)
        await update_in_batches(Session, model, {column: None}, field == value)


async def drop_old(now: datetime, usage_days: int, changes_days: int) -> None:
    """AI usage and limit hits older than `usage_days`, limit changes older than `changes_days`,
    deleted a batch at a time."""
    before = now - timedelta(days=usage_days)

    for model in (AiUsage, LimitHit):
        await delete_in_batches(Session, model, model.occurred_at < before)

    before = now - timedelta(days=changes_days)
    await delete_in_batches(Session, LimitChange, LimitChange.changed_at < before)
