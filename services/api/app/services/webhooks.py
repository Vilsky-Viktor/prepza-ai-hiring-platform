import asyncio
import json
import logging
import socket
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

import httpx
from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from prepza_common.encryption import decrypt
from prepza_common.notifications import NotificationKind, Recipient, notification
from prepza_common.public_urls import public_address
from pydantic import BaseModel

from app.config.settings import settings
from app.constants.api import API_PAGE, RETRY_BATCH, RETRY_GIVE_UP, RETRY_RUN_SECONDS
from app.constants.events import CANDIDATE_REMOVED, INTERVIEW_READY, TEST_EVENT
from app.helpers.public import candidate_of, interview_of
from app.helpers.webhooks import body_of, retry_delay, signature
from app.integrations import companies
from app.integrations import webhooks as endpoints
from app.models.api import Webhook, WebhookRetry
from app.schemas.public import CandidateEvent, InterviewEvent, RemovedEvent
from app.storage import webhook_log, webhooks
from app.storage import webhook_retries as retries

logger = logging.getLogger(__name__)


async def send(
    event_type: str,
    company_id: UUID,
    event_id: str,
    occurred_at: datetime,
    build: Callable[[], Awaitable[BaseModel | None]],
) -> None:
    """Sends an event to each of the company's web hooks, once, while whoever added it is still
    an owner or admin; `build` makes its data, or None when there's nothing to tell any more.
    Web hooks that already got it are skipped, so a redelivered event reaches only the ones
    that failed. A web hook that doesn't take it is left to the retry job, and the event is
    done: a company's failing endpoint doesn't hold up Pub/Sub for everyone. A paused one
    (`failing`) gets nothing until a test event goes through."""
    working = [hook for hook in await webhooks.of_company(company_id) if not hook.failing]
    got = await webhooks.delivered_to([hook.id for hook in working], event_id)
    hooks = [hook for hook in working if hook.id not in got]
    # A web hook works while whoever added it is still an owner or admin, like an API key.
    editors = {
        maker: (await companies.access(company_id, maker))["editor"]
        for maker in {hook.created_by for hook in hooks}
    }

    for hook in hooks:
        await mark_stopped(hook, not editors[hook.created_by])

    hooks = [hook for hook in hooks if editors[hook.created_by]]

    if not hooks:
        return

    data = await build()

    if data is None:
        return

    body = body_of(event_id, event_type, jsonable_encoder(data), occurred_at)
    # All at once, so slow endpoints together stay within Pub/Sub's acknowledgement deadline.
    taken = await asyncio.gather(*(deliver(hook, event_id, body) for hook in hooks))
    next_at = datetime.now(UTC) + retry_delay(1)

    for hook, ok in zip(hooks, taken, strict=True):
        if not ok:
            await retries.add(hook.id, event_id, body.decode(), next_at)


async def candidate_event(
    event_type: str, data: dict, event_id: str, occurred_at: datetime
) -> None:
    """A candidate finished, started, wasn't reached or expired: the interview and the
    candidate as they are now."""
    company_id = UUID(data["company_id"])
    interview_id, invite_id = UUID(data["interview_id"]), UUID(data["candidate_invite_id"])

    async def build() -> CandidateEvent | None:
        try:
            interview = await companies.interview(company_id, interview_id)
            candidate = await companies.candidate(company_id, interview_id, invite_id)
        except HTTPException as error:
            # The interview or the candidate is gone since: nothing to tell. Any other refusal
            # (busy, unavailable) raises, so Pub/Sub sends the event again; nothing was sent.
            if error.status_code != status.HTTP_404_NOT_FOUND:
                raise

            return None

        return CandidateEvent(
            interview=interview_of(interview),
            candidate=candidate_of(candidate, company_id, interview_id, settings.site_url),
        )

    await send(event_type, company_id, event_id, occurred_at, build)


async def removed(data: dict, event_id: str, occurred_at: datetime) -> None:
    """A candidate was removed: who it was, from the event itself, as the candidate is gone."""

    async def build() -> RemovedEvent:
        return RemovedEvent(
            interview_id=data["interview_id"],
            candidate_id=data["candidate_invite_id"],
            email=data["email"],
        )

    await send(CANDIDATE_REMOVED, UUID(data["company_id"]), event_id, occurred_at, build)


async def interview_ready(data: dict, event_id: str, occurred_at: datetime) -> None:
    company_id, interview_id = UUID(data["company_id"]), UUID(data["interview_id"])

    async def build() -> InterviewEvent | None:
        try:
            interview = await companies.interview(company_id, interview_id)
        except HTTPException as error:
            if error.status_code != status.HTTP_404_NOT_FOUND:
                raise

            return None

        return InterviewEvent(interview=interview_of(interview))

    await send(INTERVIEW_READY, company_id, event_id, occurred_at, build)


async def test(hook: Webhook) -> bool:
    """A signed test event, sent now, whether the web hook took it; its log shows it too."""
    event_id = str(uuid4())

    return await deliver(hook, event_id, body_of(event_id, TEST_EVENT, {}, datetime.now(UTC)))


async def retry() -> int:
    """Every 5 minutes: events web hooks didn't take, whose time came, are sent again, a batch
    at once, batch after batch until RETRY_RUN_SECONDS into the run. One with nowhere to go any
    more (it got there since, or whoever added the web hook is no longer an owner or admin) is
    dropped. One that fails again waits twice as long; after RETRY_GIVE_UP it's dropped and its
    web hook is paused. How many were due."""
    stop_at = time.monotonic() + RETRY_RUN_SECONDS
    due = 0

    while time.monotonic() < stop_at:
        sent = await retry_batch()
        due += sent

        if sent < RETRY_BATCH:
            break

    return due


async def retry_batch() -> int:
    """One batch of retries, sent at once; how many there were."""
    claimed = await retries.claim(RETRY_BATCH)
    # A web hook works while whoever added it is still an owner or admin. Companies not
    # answering fails the run: what it claimed comes back after RETRY_LEASE.
    editors = {}

    for _, hook in claimed:
        maker = (hook.company_id, hook.created_by)

        if maker not in editors:
            editors[maker] = (await companies.access(*maker))["editor"]

    await asyncio.gather(
        *(resend(row, hook, editors[(hook.company_id, hook.created_by)]) for row, hook in claimed)
    )

    return len(claimed)


async def mark_stopped(hook: Webhook, stopped: bool) -> None:
    """A web hook whose member is no longer an owner or admin stops, and the company is told,
    once; it works again once its member is an editor again. A lost notification is better than
    a failed delivery."""
    if hook.stopped == stopped:
        return

    notice = notification(
        Recipient.COMPANY,
        hook.company_id,
        NotificationKind.WEBHOOK_STOPPED,
        API_PAGE.format(company_id=hook.company_id),
        url=hook.url,
    )
    await webhooks.set_stopped(hook.id, stopped, notice if stopped else None)


async def resend(row: WebhookRetry, hook: Webhook, editor: bool) -> None:
    await mark_stopped(hook, not editor)

    if not editor or await webhooks.delivered(hook.id, row.event_id):
        await retries.remove(hook.id, row.event_id)

        return

    if await deliver(hook, row.event_id, row.body.encode()):
        await retries.remove(hook.id, row.event_id)

        return

    now = datetime.now(UTC)

    if now - row.created_at >= RETRY_GIVE_UP:
        logger.warning("Web hook %s didn't take %s for days: paused", hook.id, row.event_id)
        await retries.remove(hook.id, row.event_id)
        await webhooks.set_failing(hook.id, True)

        return

    attempts = row.attempts + 1
    await retries.postpone(hook.id, row.event_id, attempts, now + retry_delay(attempts))


async def deliver(hook: Webhook, event_id: str, body: bytes) -> bool:
    """Sends the event to one web hook; whether it took it (one that does no longer shows as
    failing). An address that no longer leads to the public internet is skipped as taken:
    retrying can't help. An address that doesn't resolve now, or a secret that can't be read
    (API_ENCRYPTION_KEY lost the key that sealed it), is a failure, retried like a refused send,
    so the web hook shows as failing rather than missing events unseen."""
    secret = decrypt(settings.api_encryption_key, hook.secret)

    try:
        address = await asyncio.to_thread(public_address, hook.url)
    except socket.gaierror as error:
        logger.info(
            "Web hook %s didn't take %s: address lookup failed: %s", hook.id, event_id, error
        )
        await log(hook, event_id, body, False, "address not found")

        return False

    if secret is None:
        logger.error("Web hook %s's secret can't be read with API_ENCRYPTION_KEY", hook.id)
        await log(hook, event_id, body, False, "secret unreadable")

        return False

    if address is None:
        logger.warning("Skipped web hook %s: non-public address", hook.id)
        await log(hook, event_id, body, True, "skipped")

        return True

    try:
        await endpoints.post(hook.url, address, body, signature(secret, int(time.time()), body))
    except httpx.HTTPError as error:
        # Not the error's text: it can carry the web hook's URL, and a URL can carry a secret.
        reason = (
            error.response.status_code
            if isinstance(error, httpx.HTTPStatusError)
            else type(error).__name__
        )
        logger.info("Web hook %s didn't take %s: %s", hook.id, event_id, reason)
        await log(hook, event_id, body, False, str(reason))

        return False

    await webhooks.mark_delivered(hook.id, event_id)
    await log(hook, event_id, body, True, "delivered")

    if hook.failing:
        await webhooks.set_failing(hook.id, False)

    return True


async def log(hook: Webhook, event_id: str, body: bytes, ok: bool, result: str) -> None:
    """Into the web hook's delivery log: its event's type, read from the body it was sent."""
    await webhook_log.add(hook.id, event_id, json.loads(body)["type"], ok, result)
