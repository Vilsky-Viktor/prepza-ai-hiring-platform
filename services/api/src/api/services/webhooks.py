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
from pydantic import BaseModel
from testee_common.auth.encryption import decrypt
from testee_common.http.public_urls import resolved_address

from api.config import settings
from api.constants.events import CANDIDATE_REMOVED, INTERVIEW_READY, TEST_EVENT
from api.core.db import Session
from api.helpers.public import candidate_of, interview_of
from api.helpers.webhooks import body_of, retry_delay, signature
from api.integrations import companies
from api.integrations import webhooks as endpoints
from api.models.api import Webhook
from api.repositories import webhook_log, webhooks
from api.repositories import webhook_retries as retries
from api.schemas.public import CandidateEvent, InterviewEvent, RemovedEvent

logger = logging.getLogger(__name__)
# How a send that went through shows in its web hook's log.
DELIVERED = "delivered"


async def send(
    event_type: str,
    company_id: UUID,
    event_id: str,
    occurred_at: datetime,
    build: Callable[[], Awaitable[BaseModel | None]],
) -> None:
    """Sends an event to each of the company's web hooks, once; `build` makes its data, or None when there's nothing to tell any more.
    Web hooks that already got it are skipped, so a redelivered event reaches only the ones
    that failed. A web hook that doesn't take it is left to the retry job, and the event is
    done: a company's failing endpoint doesn't hold up Pub/Sub for everyone. A paused one
    (`failing`) gets nothing until a test event goes through."""
    async with Session() as session:
        working = [
            hook for hook in await webhooks.of_company(session, company_id) if not hook.failing
        ]
        got = await webhooks.delivered_to(session, [hook.id for hook in working], event_id)

    hooks = [hook for hook in working if hook.id not in got]

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
            async with Session.begin() as session:
                await retries.add(session, hook.id, event_id, body.decode(), next_at)


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


async def deliver(hook: Webhook, event_id: str, body: bytes) -> bool:
    """Sends the event to one web hook; whether it took it. A send that went through is noted
    as delivered, logged and, for a paused web hook, starts it again, all in one save; any
    other outcome is only logged."""
    ok, result = await attempt(hook, event_id, body)
    event_type = json.loads(body)["type"]

    async with Session.begin() as session:
        if result == DELIVERED:
            await webhooks.mark_delivered(session, hook.id, event_id)

        await webhook_log.add(session, hook.id, event_id, event_type, ok, result)

        if result == DELIVERED and hook.failing:
            await webhooks.set_failing(session, hook.id, False)

    return ok


async def attempt(hook: Webhook, event_id: str, body: bytes) -> tuple[bool, str]:
    """Sends the event to one web hook: whether it took it, and how it went, for its log. An
    address that no longer leads to the public internet is skipped as taken: retrying can't
    help. An address that doesn't resolve now, or a secret that can't be read
    (API_ENCRYPTION_KEY lost the key that sealed it), is a failure, retried like a refused send,
    so the web hook shows as failing rather than missing events unseen."""
    secret = decrypt(settings.api_encryption_key, hook.secret)
    # A rolled secret's old one, while it still signs too.
    overlapping = hook.previous_secret and hook.previous_until > datetime.now(UTC)
    previous = decrypt(settings.api_encryption_key, hook.previous_secret) if overlapping else None

    try:
        address = await resolved_address(hook.url)
    except socket.gaierror as error:
        logger.info(
            "Web hook %s didn't take %s: address lookup failed: %s", hook.id, event_id, error
        )

        return False, "address not found"

    if secret is None:
        logger.error("Web hook %s's secret can't be read with API_ENCRYPTION_KEY", hook.id)

        return False, "secret unreadable"

    if address is None:
        logger.warning("Skipped web hook %s: non-public address", hook.id)

        return True, "skipped"

    try:
        secrets = [secret, previous] if previous else [secret]
        await endpoints.post(hook.url, address, body, signature(secrets, int(time.time()), body))
    except httpx.HTTPError as error:
        # Not the error's text: it can carry the web hook's URL, and a URL can carry a secret.
        reason = (
            error.response.status_code
            if isinstance(error, httpx.HTTPStatusError)
            else type(error).__name__
        )
        logger.info("Web hook %s didn't take %s: %s", hook.id, event_id, reason)

        return False, str(reason)

    return True, DELIVERED
