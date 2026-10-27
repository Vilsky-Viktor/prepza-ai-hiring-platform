import uuid
from datetime import UTC, datetime

from prepza_common.events import audit, outbox
from prepza_common.events.audit_actions import AuditAction, TargetKind
from prepza_common.events.notifications import NOTIFICATION_REQUESTED
from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert

from api.constants.api import DELIVERIES_KEPT
from api.core.db import Session
from api.helpers.webhooks import masked
from api.models.api import Webhook, WebhookDelivery, WebhookRetry
from api.models.outbox import OutboxEvent


def company_of(webhook_id: uuid.UUID):
    """The web hook's company, read by the statement that saves its row."""
    return select(Webhook.company_id).where(Webhook.id == webhook_id).scalar_subquery()


async def of_company(company_id: uuid.UUID) -> list[Webhook]:
    """Oldest first."""
    query = select(Webhook).where(Webhook.company_id == company_id).order_by(Webhook.created_at)

    async with Session() as session:
        return list(await session.scalars(query))


async def add(
    company_id: uuid.UUID, url: str, sealed_secret: str, user_id: str, limit: int
) -> Webhook | None:
    """None when the company already has `limit` web hooks. One company's web hooks are added
    one at a time, so two at once can't both pass the count. The company's action log gets it
    as `user_id`'s, by its site only (masked)."""
    count = select(func.count()).select_from(Webhook).where(Webhook.company_id == company_id)
    hook = Webhook(company_id=company_id, url=url, secret=sealed_secret, created_by=user_id)

    async with Session() as session:
        await session.execute(
            select(func.pg_advisory_xact_lock(func.hashtext(f"webhooks:{company_id}")))
        )

        if await session.scalar(count) >= limit:
            return None

        session.add(hook)
        await session.flush()
        audit.add(
            session,
            OutboxEvent,
            company_id,
            user_id,
            AuditAction.WEBHOOK_ADDED,
            TargetKind.WEBHOOK,
            hook.id,
            masked(url),
        )
        await session.commit()
        await session.refresh(hook)

    return hook


async def get(company_id: uuid.UUID, webhook_id: uuid.UUID) -> Webhook | None:
    """The company's web hook, or None for one of another company."""
    async with Session() as session:
        return await session.scalar(
            select(Webhook).where(Webhook.company_id == company_id, Webhook.id == webhook_id)
        )


async def remove(company_id: uuid.UUID, webhook_id: uuid.UUID, user_id: str) -> bool:
    """Whether there was such a web hook of the company; what it got goes with it. The
    company's action log gets it as `user_id`'s."""
    query = (
        delete(Webhook)
        .where(Webhook.company_id == company_id, Webhook.id == webhook_id)
        .returning(Webhook.url)
    )

    async with Session() as session:
        url = await session.scalar(query)

        if url is not None:
            audit.add(
                session,
                OutboxEvent,
                company_id,
                user_id,
                AuditAction.WEBHOOK_DELETED,
                TargetKind.WEBHOOK,
                webhook_id,
                masked(url),
            )

        await session.commit()

    return url is not None


async def rotate(
    company_id: uuid.UUID, webhook_id: uuid.UUID, sealed_secret: str, until: datetime, user_id: str
) -> Webhook | None:
    """Gives the company's web hook a new secret; the current one keeps signing too until
    `until` (a secret rolled again meanwhile ends the older one's overlap). The company's action
    log gets it as `user_id`'s, in the same transaction. None when there's no such web hook."""
    query = (
        update(Webhook)
        .where(Webhook.company_id == company_id, Webhook.id == webhook_id)
        .values(previous_secret=Webhook.secret, previous_until=until, secret=sealed_secret)
        .returning(Webhook)
    )

    async with Session() as session:
        hook = await session.scalar(query)

        if hook is not None:
            audit.add(
                session,
                OutboxEvent,
                company_id,
                user_id,
                AuditAction.WEBHOOK_SECRET_ROTATED,
                TargetKind.WEBHOOK,
                webhook_id,
                masked(hook.url),
            )

        await session.commit()

    return hook


async def tested(hook: Webhook, user_id: str) -> None:
    """A member sent the web hook a test event: the company's action log gets it."""
    async with Session() as session:
        audit.add(
            session,
            OutboxEvent,
            hook.company_id,
            user_id,
            AuditAction.WEBHOOK_TESTED,
            TargetKind.WEBHOOK,
            hook.id,
            masked(hook.url),
        )
        await session.commit()


async def remove_company(company_id: uuid.UUID) -> None:
    async with Session() as session:
        await session.execute(delete(Webhook).where(Webhook.company_id == company_id))
        await session.commit()


async def of_user(user_id: str) -> list[Webhook]:
    async with Session() as session:
        return list(await session.scalars(select(Webhook).where(Webhook.created_by == user_id)))


async def remove_user(user_id: str) -> None:
    async with Session() as session:
        await session.execute(delete(Webhook).where(Webhook.created_by == user_id))
        await session.commit()


async def delivered_to(webhook_ids: list[uuid.UUID], event_id: str) -> set[uuid.UUID]:
    """Those of the web hooks that already got the event."""
    query = select(WebhookDelivery.webhook_id).where(
        WebhookDelivery.webhook_id.in_(webhook_ids), WebhookDelivery.event_id == event_id
    )

    async with Session() as session:
        return set(await session.scalars(query))


async def delivered(webhook_id: uuid.UUID, event_id: str) -> bool:
    query = select(WebhookDelivery).where(
        WebhookDelivery.webhook_id == webhook_id, WebhookDelivery.event_id == event_id
    )

    async with Session() as session:
        return await session.scalar(query) is not None


async def mark_delivered(webhook_id: uuid.UUID, event_id: str) -> None:
    """Notes the event as sent to the web hook, and forgets the web hook's ones long past
    redelivery (DELIVERIES_KEPT)."""
    old = delete(WebhookDelivery).where(
        WebhookDelivery.webhook_id == webhook_id,
        WebhookDelivery.delivered_at < datetime.now(UTC) - DELIVERIES_KEPT,
    )
    query = (
        insert(WebhookDelivery)
        .values(webhook_id=webhook_id, event_id=event_id, company_id=company_of(webhook_id))
        .on_conflict_do_nothing()
    )

    async with Session() as session:
        await session.execute(old)
        await session.execute(query)
        await session.commit()


async def set_failing(webhook_id: uuid.UUID, failing: bool) -> None:
    """Pauses the web hook (it dropped an event after RETRY_GIVE_UP), with its other events
    waiting for a retry, or starts it again (it took an event: a test event)."""
    query = update(Webhook).where(Webhook.id == webhook_id).values(failing=failing)

    async with Session() as session:
        await session.execute(query)

        if failing:
            await session.execute(delete(WebhookRetry).where(WebhookRetry.webhook_id == webhook_id))

        await session.commit()


async def set_stopped(webhook_id: uuid.UUID, stopped: bool, notice: dict | None = None) -> bool:
    """True when it changed just now: of several events at once, only one tells the company,
    with `notice` (a notification's data), sent through the outbox with the change."""
    query = (
        update(Webhook)
        .where(Webhook.id == webhook_id, Webhook.stopped.is_not(stopped))
        .values(stopped=stopped)
        .returning(Webhook.id)
    )

    async with Session() as session:
        changed = await session.scalar(query)

        if changed is not None and notice is not None:
            outbox.add(session, OutboxEvent, NOTIFICATION_REQUESTED, notice)

        await session.commit()

    return changed is not None
