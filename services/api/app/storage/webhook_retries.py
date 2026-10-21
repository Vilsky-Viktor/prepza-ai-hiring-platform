import uuid
from datetime import UTC, datetime

from sqlalchemy import cast, delete, func, select, update
from sqlalchemy.dialects.postgresql import JSONB, insert

from app.constants.api import RETRY_LEASE
from app.models.api import Webhook, WebhookRetry
from app.storage.db import Session
from app.storage.webhooks import company_of


async def add(webhook_id: uuid.UUID, event_id: str, body: str, next_at: datetime) -> None:
    """Once per web hook and event: a redelivered event keeps the retry it has."""
    query = (
        insert(WebhookRetry)
        .values(
            webhook_id=webhook_id,
            event_id=event_id,
            company_id=company_of(webhook_id),
            body=body,
            attempts=1,
            next_at=next_at,
        )
        .on_conflict_do_nothing()
    )

    async with Session() as session:
        await session.execute(query)
        await session.commit()


async def claim(limit: int) -> list[tuple[WebhookRetry, Webhook]]:
    """Up to `limit` retries whose time came, longest waiting first, with their web hooks. Each
    is put off by RETRY_LEASE in the same step, so a run at the same time doesn't take it, and a
    run cut off midway leaves it for a later one."""
    now = datetime.now(UTC)
    due = (
        select(WebhookRetry, Webhook)
        .join(Webhook, Webhook.id == WebhookRetry.webhook_id)
        .where(WebhookRetry.next_at <= now)
        .order_by(WebhookRetry.next_at)
        .limit(limit)
        .with_for_update(of=WebhookRetry, skip_locked=True)
    )

    async with Session() as session:
        found = [tuple(row) for row in await session.execute(due)]

        for retry, _ in found:
            retry.next_at = now + RETRY_LEASE

        await session.commit()

    return found


async def postpone(webhook_id: uuid.UUID, event_id: str, attempts: int, next_at: datetime) -> None:
    query = (
        update(WebhookRetry)
        .where(WebhookRetry.webhook_id == webhook_id, WebhookRetry.event_id == event_id)
        .values(attempts=attempts, next_at=next_at)
    )

    async with Session() as session:
        await session.execute(query)
        await session.commit()


async def remove(webhook_id: uuid.UUID, event_id: str) -> None:
    query = delete(WebhookRetry).where(
        WebhookRetry.webhook_id == webhook_id, WebhookRetry.event_id == event_id
    )

    async with Session() as session:
        await session.execute(query)
        await session.commit()


async def remove_candidate(company_id: uuid.UUID, interview_id: str, email: str) -> None:
    """A candidate the company erased: their results waiting to be sent again to its web hooks
    go, read from each kept body (a candidate.finished event)."""
    body = cast(WebhookRetry.body, JSONB)["data"]
    query = delete(WebhookRetry).where(
        WebhookRetry.webhook_id.in_(select(Webhook.id).where(Webhook.company_id == company_id)),
        body["interview"]["id"].astext == interview_id,
        func.lower(body["candidate"]["email"].astext) == email.lower(),
    )

    async with Session() as session:
        await session.execute(query)
        await session.commit()
