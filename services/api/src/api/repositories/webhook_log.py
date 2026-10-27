import uuid

from sqlalchemy import delete, select

from api.constants.api import WEBHOOK_LOG_KEPT
from api.core.db import Session
from api.models.api import WebhookAttempt
from api.repositories.webhooks import company_of


async def add(webhook_id: uuid.UUID, event_id: str, event_type: str, ok: bool, result: str) -> None:
    """Logs a send, keeping only the web hook's latest WEBHOOK_LOG_KEPT."""
    async with Session() as session:
        session.add(
            WebhookAttempt(
                webhook_id=webhook_id,
                event_id=event_id,
                company_id=company_of(webhook_id),
                event_type=event_type,
                ok=ok,
                result=result,
            )
        )
        await session.flush()
        latest = (
            select(WebhookAttempt.id)
            .where(WebhookAttempt.webhook_id == webhook_id)
            .order_by(WebhookAttempt.at.desc(), WebhookAttempt.id)
            .limit(WEBHOOK_LOG_KEPT)
        )
        await session.execute(
            delete(WebhookAttempt).where(
                WebhookAttempt.webhook_id == webhook_id, WebhookAttempt.id.not_in(latest)
            )
        )
        await session.commit()


async def latest(webhook_id: uuid.UUID) -> list[WebhookAttempt]:
    async with Session() as session:
        rows = await session.scalars(
            select(WebhookAttempt)
            .where(WebhookAttempt.webhook_id == webhook_id)
            .order_by(WebhookAttempt.at.desc())
        )

        return list(rows)
