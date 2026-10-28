import asyncio
import logging
import time
from collections.abc import AsyncIterator
from datetime import datetime

import anyio
import httpx
from fastapi import HTTPException, status
from prepza_common.config.constants import RATE_LIMITED, RETRY_AFTER
from prepza_common.events.notifications import EVERYONE, NotificationKind, Recipient
from prepza_common.http.sse import sse_event
from prepza_common.limits.limits import limit, record_hit
from prepza_common.limits.rate_limit import counted
from prepza_common.redis import memory_cache

from notifications.constants.notifications import (
    ACCOUNT_CREATED_KEY,
    ACCOUNT_CREATED_SECONDS,
    CHANNEL,
    COMPANY_IDS_KEY,
    COMPANY_IDS_SECONDS,
    DROPDOWN_LIMIT,
    HEARTBEAT_SECONDS,
    STREAM_REFRESH_SECONDS,
    STREAM_RETRY_SECONDS,
    STREAM_SLOT_SECONDS,
    STREAMS_LIMIT,
)
from notifications.core.db import Session
from notifications.integrations import accounts, companies, site
from notifications.integrations.redis import get_redis
from notifications.integrations.subscription import listening
from notifications.repositories import notifications
from notifications.repositories.notifications import Recipients
from notifications.schemas.notifications import FeedOut, NotificationOut

logger = logging.getLogger(__name__)


async def recipients_of(user_id: str, fresh: bool = False) -> tuple[Recipients, bool]:
    """The user's own notifications, and those of every company they belong to (kept for
    COMPANY_IDS_SECONDS, read again when `fresh`, as right after joining one); whether the
    companies are in: when companies doesn't answer, only the user's own."""
    key = COMPANY_IDS_KEY.format(user_id=user_id)
    ids = None if fresh else memory_cache.get(key)

    if ids is None:
        try:
            ids = await companies.company_ids(user_id)
        except httpx.HTTPError as error:
            logger.warning("Companies didn't say %s's companies: %s", user_id, error)

            return [(Recipient.USER, user_id)], False

        memory_cache.put(key, ids, COMPANY_IDS_SECONDS)

    own = (Recipient.USER, user_id)

    return [own, *((Recipient.COMPANY, company_id) for company_id in ids)], True


async def account_created(user_id: str) -> datetime | None:
    """When the user's account was made, from accounts (kept ACCOUNT_CREATED_SECONDS, as it
    never changes): the notifications for everyone that came after it are theirs too. None
    while accounts doesn't answer, or doesn't know: then the bell shows only their own."""
    key = ACCOUNT_CREATED_KEY.format(user_id=user_id)
    created = memory_cache.get(key)

    if created is None:
        try:
            created = await accounts.account_created(user_id)
        except httpx.HTTPError as error:
            logger.warning("Accounts didn't say when %s's account was made: %s", user_id, error)

            return None

        if created is not None:
            memory_cache.put(key, created, ACCOUNT_CREATED_SECONDS)

    return created


async def in_language(items: list[NotificationOut], language: str) -> list[NotificationOut]:
    """News posts are named in the reader's language (English until translated), and a post
    deleted meanwhile isn't shown. While site doesn't answer, they keep their English title."""
    ids = [item.data["news_id"] for item in items if item.kind == NotificationKind.NEWS]

    if not ids:
        return items

    try:
        titles = await site.news_titles(ids, language)
    except httpx.HTTPError as error:
        logger.warning("Site didn't name the news posts: %s", error)

        return items

    return [
        item.model_copy(update={"data": {**item.data, "title": titles[item.data["news_id"]]}})
        if item.kind == NotificationKind.NEWS
        else item
        for item in items
        if item.kind != NotificationKind.NEWS or item.data["news_id"] in titles
    ]


async def feed(user_id: str, language: str, fresh: bool = False) -> FeedOut:
    recipients, _ = await recipients_of(user_id, fresh)
    since = await account_created(user_id)

    async with Session() as session:
        items = await notifications.latest(session, recipients, DROPDOWN_LIMIT, since)
        unread = await notifications.unread_count(session, recipients, user_id, since)

    shown = [NotificationOut.model_validate(item) for item in items]

    return FeedOut(items=await in_language(shown, language), unread=unread)


async def announce(recipient: str, recipient_id: str) -> None:
    """Tells the recipient's open tabs, on any instance, that something new came."""
    channel = CHANNEL.format(recipient=recipient, recipient_id=recipient_id)
    await get_redis().publish(channel, "new")


async def changes(user_id: str, fresh: bool = False) -> AsyncIterator[str]:
    """Server-sent events for one open tab: {"new": true} whenever one of the user's recipients
    gets a notification, and a comment every HEARTBEAT_SECONDS so the connection stays open. The
    instance's tabs share one Redis subscription. It ends after STREAM_REFRESH_SECONDS (or
    STREAM_RETRY_SECONDS without the companies), and the tab reconnects with what's current."""
    recipients, complete = await recipients_of(user_id, fresh)
    # Everyone's notifications are announced to every open tab.
    everyone = (Recipient.ALL, EVERYONE)
    channels = [
        CHANNEL.format(recipient=kind, recipient_id=id_) for kind, id_ in [*recipients, everyone]
    ]
    ends_at = time.monotonic() + (STREAM_REFRESH_SECONDS if complete else STREAM_RETRY_SECONDS)

    async with listening(channels) as heard:
        yield ": connected\n\n"

        while time.monotonic() < ends_at:
            try:
                await asyncio.wait_for(heard.wait(), HEARTBEAT_SECONDS)
            except TimeoutError:
                yield ": heartbeat\n\n"

                continue

            heard.clear()

            yield sse_event({"new": True})


async def open_stream(user_id: str, fresh: bool = False) -> AsyncIterator[str]:
    """One open tab's stream, in one of the user's STREAMS_PER_USER slots (a limit edited in the
    Controls); refused (429, Retry-After the bell's own retry) when they're all taken, and
    recorded. The slot is given back when the stream ends. The count and its expiry are set in
    one transaction (rate_limit.counted), so a crash never leaves it without one; slots a crash
    left free themselves after STREAM_SLOT_SECONDS."""
    key = f"streams:user:{user_id}"
    redis = get_redis()
    most = await limit(redis, STREAMS_LIMIT)
    taken, _ = await counted(redis, key, 1, STREAM_SLOT_SECONDS)

    if taken > most:
        await counted(redis, key, -1, STREAM_SLOT_SECONDS)
        await record_hit(STREAMS_LIMIT, user_id=user_id)

        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            RATE_LIMITED,
            headers={RETRY_AFTER: str(STREAM_RETRY_SECONDS)},
        )

    return in_slot(key, changes(user_id, fresh))


async def in_slot(key: str, stream: AsyncIterator[str]) -> AsyncIterator[str]:
    try:
        async for chunk in stream:
            yield chunk
    finally:
        # A tab closing cancels the response; shielded, the slot is still given back.
        with anyio.CancelScope(shield=True):
            await counted(get_redis(), key, -1, STREAM_SLOT_SECONDS)
