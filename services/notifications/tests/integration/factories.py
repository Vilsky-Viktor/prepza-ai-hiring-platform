import base64
import hashlib
import hmac
import json
import time
import uuid

import httpx
from prepza_common.constants import EVENT_ID_ATTRIBUTE
from prepza_common.notifications import NotificationKind, Recipient, notification

from app.main import app
from app.models.outbox import OutboxEvent
from app.storage.db import Session


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


def push(event_type: str, data: dict, outbox_id: str | None = None, message_id: str = "m-1"):
    """A Pub/Sub push of one event; an outbox event carries its own id as an attribute."""
    attributes = {"type": event_type, **({EVENT_ID_ATTRIBUTE: outbox_id} if outbox_id else {})}

    return {
        "message": {
            "data": base64.b64encode(json.dumps(data).encode()).decode(),
            "attributes": attributes,
            "messageId": message_id,
        },
        "subscription": "projects/demo-test/subscriptions/notifications-events",
    }


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
    Its test keeps the request from publishing (webhook_routes.outbox_service.flush_quietly)."""
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
