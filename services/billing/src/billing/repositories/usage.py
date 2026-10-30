"""Every AI call and limit hit the services record, stored once each (by event id)."""

from datetime import datetime, timedelta
from decimal import Decimal

from prepza_common.ai.ai_constants import Category
from prepza_common.db.db import delete_in_batches, update_in_batches
from sqlalchemy import exists, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from billing.constants.products import OwnerType
from billing.models.billing import Purchase
from billing.models.limits import LimitChange
from billing.models.usage import AiUsage, LimitHit

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


async def company_paid(session: AsyncSession, company_id: str, by: datetime) -> bool:
    """Whether the company had topped up by `by`."""
    return await session.scalar(
        select(
            exists().where(
                Purchase.owner_type == OwnerType.COMPANY,
                Purchase.owner_id == company_id,
                Purchase.created_at <= by,
            )
        )
    )


async def store_usage(
    session: AsyncSession, event_id: str, occurred_at: datetime, data: dict, category: Category
) -> bool:
    """Stores one AI call, for whom `category` says; False when the event was stored before."""
    values = {field: data.get(field) for field in USAGE_FIELDS}
    # The event's float cost, exactly: its shortest decimal form.
    values["cost"] = Decimal(str(data.get("cost_usd") or 0))
    stored = await session.scalar(
        insert(AiUsage)
        .values(event_id=event_id, occurred_at=occurred_at, category=category, **values)
        .on_conflict_do_nothing(index_elements=["event_id"])
        .returning(AiUsage.id)
    )

    return stored is not None


async def store_hit(
    session: AsyncSession, event_id: str, occurred_at: datetime, data: dict
) -> None:
    values = {field: data.get(field) for field in HIT_FIELDS}
    await session.execute(
        insert(LimitHit)
        .values(event_id=event_id, occurred_at=occurred_at, **values)
        .on_conflict_do_nothing(index_elements=["event_id"])
    )


async def forget(sessions, column: str, value: str) -> None:
    """Empties a deleted account's or company's id in both tables, a batch at a time, each
    batch its own transaction from the factory `sessions`; the costs and hits stay."""
    for model in (AiUsage, LimitHit):
        field = getattr(model, column)
        await update_in_batches(sessions, model, {column: None}, field == value)


async def drop_old(sessions, now: datetime, usage_days: int, changes_days: int) -> None:
    """AI usage and limit hits older than `usage_days`, limit changes older than `changes_days`,
    deleted a batch at a time, each batch its own transaction from the factory `sessions`."""
    before = now - timedelta(days=usage_days)

    for model in (AiUsage, LimitHit):
        await delete_in_batches(sessions, model, model.occurred_at < before)

    before = now - timedelta(days=changes_days)
    await delete_in_batches(sessions, LimitChange, LimitChange.changed_at < before)


async def of_user(session: AsyncSession, user_id: str) -> tuple[list[AiUsage], list[LimitHit]]:
    """The user's AI calls and limit hits still kept (13 months at most), for their export,
    oldest first."""
    calls = await session.scalars(
        select(AiUsage).where(AiUsage.user_id == user_id).order_by(AiUsage.occurred_at)
    )
    hits = await session.scalars(
        select(LimitHit).where(LimitHit.user_id == user_id).order_by(LimitHit.occurred_at)
    )

    return list(calls), list(hits)
