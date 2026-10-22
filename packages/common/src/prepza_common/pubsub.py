import asyncio
import base64
import json
import logging
import os
import uuid
from datetime import UTC, datetime

from prepza_common import http
from prepza_common.backoff import wait_seconds
from prepza_common.constants import (
    EVENT_ID_ATTRIBUTE,
    EVENTS_TOPIC,
    HTTP_TIMEOUT_SECONDS,
    OCCURRED_AT_ATTRIBUTE,
    PUBLISH_RETRY_FIRST_WAIT,
    PUBSUB_URL,
)
from prepza_common.google import access_token, project, running_locally
from pydantic import BaseModel

logger = logging.getLogger(__name__)


def message(
    event_type: str,
    data: dict,
    event_id: str | None = None,
    occurred_at: datetime | None = None,
) -> dict:
    """One event as Pub/Sub takes it, with its own id: `event_id` when given (it stays the same on
    a re-send), otherwise a new one. Consumers never fall back on Pub/Sub's message id, which the
    local emulator numbers from 1 again after a restart, so a new event could look like one already
    handled and be dropped."""
    attributes = {
        "type": event_type,
        EVENT_ID_ATTRIBUTE: event_id or uuid.uuid4().hex,
        OCCURRED_AT_ATTRIBUTE: (occurred_at or datetime.now(UTC)).isoformat(),
    }

    return {"data": base64.b64encode(json.dumps(data).encode()).decode(), "attributes": attributes}


async def publish_batch(messages: list[dict], timeout: float = HTTP_TIMEOUT_SECONDS) -> None:
    """Publishes events to the `events` topic in one call; Pub/Sub takes all or none. Each
    consumer gets them pushed to its /internal/events, and Pub/Sub retries until they're handled.
    Locally they go to the emulator."""
    headers = {}

    if running_locally():
        base = f"http://{os.environ['PUBSUB_EMULATOR_HOST']}"
    else:
        base = PUBSUB_URL
        headers["Authorization"] = f"Bearer {await asyncio.to_thread(access_token)}"

    response = await http.get_client().post(
        f"{base}/v1/projects/{project()}/topics/{EVENTS_TOPIC}:publish",
        json={"messages": messages},
        headers=headers,
        timeout=timeout,
    )

    response.raise_for_status()


async def publish(event_type: str, data: dict, timeout: float = HTTP_TIMEOUT_SECONDS) -> None:
    """Publishes one domain event (see publish_batch)."""
    await publish_batch([message(event_type, data)], timeout)


async def publish_retried(event_type: str, data: dict, attempts: int, timeout: float) -> None:
    """Publishes one event that has no outbox (a record of an AI call or a limit hit): tried up
    to `attempts` times under one id, so a try that reached Pub/Sub after all is stored once,
    with a jittered wait between tries (callers that failed together don't retry together), all
    within `timeout` seconds, as the request it's recorded in waits for it; then given up and
    logged, never raised."""
    sent = message(event_type, data)
    deadline = asyncio.get_running_loop().time() + timeout

    for attempt in range(1, attempts + 1):
        left = deadline - asyncio.get_running_loop().time()

        try:
            async with asyncio.timeout(left):
                await publish_batch([sent], left)

            return
        except Exception:
            wait = wait_seconds(PUBLISH_RETRY_FIRST_WAIT, attempt - 1)

            if attempt == attempts or wait >= deadline - asyncio.get_running_loop().time():
                logger.warning("Couldn't publish %s", event_type, exc_info=True)

                return

            await asyncio.sleep(wait)


class PushMessage(BaseModel):
    data: str = ""
    attributes: dict[str, str] = {}
    messageId: str
    publishTime: str | None = None


class PushBody(BaseModel):
    """What Pub/Sub sends to a push endpoint."""

    message: PushMessage
    subscription: str


def event_of(body: PushBody) -> tuple[str, dict, str]:
    """The event's type, its data, and its id: the outbox's id, the same however often the event
    is re-sent, or else Pub/Sub's (the same across Pub/Sub's own retries)."""
    data = json.loads(base64.b64decode(body.message.data)) if body.message.data else {}
    attributes = body.message.attributes
    event_id = attributes.get(EVENT_ID_ATTRIBUTE) or body.message.messageId

    return attributes.get("type", ""), data, event_id


def occurred_at(body: PushBody) -> datetime:
    """When the change behind the event happened: its outbox row's time, else when Pub/Sub got
    it (events published before the attribute existed)."""
    stamp = body.message.attributes.get(OCCURRED_AT_ATTRIBUTE) or body.message.publishTime

    return datetime.fromisoformat(stamp) if stamp else datetime.now(UTC)
