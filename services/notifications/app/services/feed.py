import asyncio
import logging
import time
from collections.abc import AsyncIterator
from datetime import datetime

import anyio
import httpx
from fastapi import HTTPException, status
from prepza_common import memory_cache
from prepza_common.constants import RATE_LIMITED
from prepza_common.notifications import EVERYONE, NotificationKind, Recipient
from prepza_common.sse import sse_event

from app.constants.notifications import (
    ACCOUNT_CREATED_KEY,
    ACCOUNT_CREATED_SECONDS,
    CHANNEL,
    COMPANY_IDS_KEY,
    COMPANY_IDS_SECONDS,
    DROPDOWN_LIMIT,
    HEARTBEAT_SECONDS,
    MAX_STREAMS_PER_USER,
    STREAM_REFRESH_SECONDS,
    STREAM_RETRY_SECONDS,
    STREAM_SLOT_SECONDS,
)
from app.integrations import companies, library
from app.integrations.redis import get_redis
from app.integrations.subscription import listening
from app.schemas.notifications import FeedOut, NotificationOut
from app.storage import notifications
from app.storage.notifications import Recipients

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
    """When the user's account was made, from library (kept ACCOUNT_CREATED_SECONDS, as it
    never changes): the notifications for everyone that came after it are theirs too. None
    while library doesn't answer, or doesn't know: then the bell shows only their own."""
    key = ACCOUNT_CREATED_KEY.format(user_id=user_id)
    created = memory_cache.get(key)

    if created is None:
        try:
            created = await library.account_created(user_id)
        except httpx.HTTPError as error:
            logger.warning("Library didn't say when %s's account was made: %s", user_id, error)

            return None

        if created is not None:
            memory_cache.put(key, created, ACCOUNT_CREATED_SECONDS)

    return created


async def in_language(items: list[NotificationOut], language: str) -> list[NotificationOut]:
    """News posts are named in the reader's language (English until translated), and a post
    deleted meanwhile isn't shown. While library doesn't answer, they keep their English title."""
    ids = [item.data["news_id"] for item in items if item.kind == NotificationKind.NEWS]

    if not ids:
        return items

    try:
        titles = await library.news_titles(ids, language)
    except httpx.HTTPError as error:
        logger.warning("Library didn't name the news posts: %s", error)

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
    items = await notifications.latest(recipients, DROPDOWN_LIMIT, since)
    shown = [NotificationOut.model_validate(item) for item in items]

    return FeedOut(
        items=await in_language(shown, language),
        unread=await notifications.unread_count(recipients, user_id, since),
    )


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
    """One open tab's stream, in one of the user's MAX_STREAMS_PER_USER slots; refused (429)
    when they're all taken. The slot is given back when the stream ends."""
    key = f"streams:user:{user_id}"
    redis = get_redis()
    taken = await redis.incr(key)

    # A refused tab doesn't keep the slots alive: only a granted one renews their expiry.
    if taken > MAX_STREAMS_PER_USER:
        await redis.decr(key)

        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, RATE_LIMITED)

    await redis.expire(key, STREAM_SLOT_SECONDS)

    return in_slot(key, changes(user_id, fresh))


async def in_slot(key: str, stream: AsyncIterator[str]) -> AsyncIterator[str]:
    try:
        async for chunk in stream:
            yield chunk
    finally:
        # A tab closing cancels the response; shielded, the slot is still given back.
        with anyio.CancelScope(shield=True):
            await get_redis().decr(key)
