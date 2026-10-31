import base64
import hashlib
import hmac
import time
import uuid

import httpx
from event_pushes import push
from fastapi import HTTPException
from testee_common.events.notifications import NotificationKind, Recipient, notification

from notifications.constants.campaigns import ONE_A_DAY
from notifications.core.db import Session
from notifications.main import app
from notifications.models.outbox import OutboxEvent
from notifications.repositories import bulk_sends
from notifications.services import campaign_sends


def company() -> str:
    """A company of its own for each test: the database is shared by the whole run."""
    return str(uuid.uuid4())


def finished(company_id: str, title: str = "Backend", **data) -> dict:
    """A "candidate finished" notification for the company, about its test `title`."""
    return notification(
        Recipient.COMPANY,
        company_id,
        NotificationKind.CANDIDATE_FINISHED,
        f"/companies/{company_id}",
        title=title,
        **data,
    )


def api() -> httpx.AsyncClient:
    """The app itself, called in the test's own event loop; a failing route answers 500."""
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)

    return httpx.AsyncClient(transport=transport, base_url="http://notifications")


def signed(body: bytes, secret: str, delivery_id: str | None = None) -> dict:
    """Headers of a webhook signed as Resend (Svix) signs it with the `whsec_` secret, as its
    delivery `delivery_id` (svix-id): a new one unless given, so no test's delivery is another's
    (they're recorded once each)."""
    delivery_id = delivery_id or f"msg_{uuid.uuid4().hex}"
    timestamp = str(int(time.time()))
    key = base64.b64decode(secret.removeprefix("whsec_"))
    digest = hmac.new(key, f"{delivery_id}.{timestamp}.".encode() + body, hashlib.sha256).digest()

    return {
        "svix-id": delivery_id,
        "svix-timestamp": timestamp,
        "svix-signature": "v1," + base64.b64encode(digest).decode(),
        "content-type": "application/json",
    }


async def receive(
    client, secret: str, body: bytes, delivery_id: str | None = None
) -> tuple[int, int | None]:
    """Resend's web hook signed with `secret` (its own delivery unless given), then its recorded
    event pushed back as Pub/Sub does: both answers' statuses (None when nothing was recorded).
    Its test keeps the request from publishing (outbox_service.flush_quietly)."""
    headers = signed(body, secret, delivery_id)
    answered = await client.post("/webhooks/resend", content=body, headers=headers)
    event_id = uuid.uuid5(uuid.NAMESPACE_URL, f"resend:{headers['svix-id']}")

    async with Session() as session:
        recorded = await session.get(OutboxEvent, event_id)

    if recorded is None:
        return answered.status_code, None

    pushed = await client.post(
        "/internal/events", json=push(recorded.event_type, recorded.data, str(event_id))
    )

    return answered.status_code, pushed.status_code


async def marked_sent(campaign_id: uuid.UUID, kind: str, asked_by: str, per_day: int):
    """Marks the campaign sent as sending it does (campaign_sends.mark_sent): its bulk send's id,
    or why it wasn't (ALREADY_SENT, CHANGED, ONE_A_DAY)."""
    try:
        sent = await campaign_sends.mark_sent(campaign_id, kind, asked_by, per_day)
    except HTTPException as refused:
        return refused.detail

    if not sent:
        return ONE_A_DAY

    async with Session() as session:
        return (await bulk_sends.get(session, kind, str(campaign_id))).id
