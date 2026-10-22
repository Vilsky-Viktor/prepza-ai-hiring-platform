# The bulk sender: legal notices and campaigns, to many users at once. A send's recipients are
# worked out a page at a time (prepare) and saved; each run then sends the next pending ones, each claimed
# under a lock, paced under Resend's per-second limit and within its daily quota.
import asyncio
import logging
import time
from datetime import UTC, datetime

from prepza_common import redis_lock
from prepza_common.limits import limit, record_hit
from prepza_common.paging import ID_PAGE_SIZE

from app.constants.bulk import (
    BULK_BATCH,
    BULK_LOCK_KEY,
    BULK_LOCK_SECONDS,
    CAMPAIGN_KINDS,
    LEGAL_KINDS,
    MAX_ATTEMPTS,
    MAX_REASON_LENGTH,
    RecipientStatus,
    SkipReason,
)
from app.constants.member_emails import SEND_INTERVAL_SECONDS
from app.helpers.unsubscribe import address_hash
from app.integrations import library
from app.integrations.redis import get_redis
from app.integrations.resend import EmailRefused, ResendBusy
from app.models.bulk import BulkSend
from app.services import delivery
from app.services.bulk_content import (
    audience_page,
    campaign_texts,
    email_for,
    legal_in_bell,
    without_guests,
)
from app.services.member_sends import deadline
from app.storage import bulk_recipients, bulk_sends, suppressed

logger = logging.getLogger(__name__)


async def prepare(send: BulkSend, until: float) -> None:
    """Works out the send's recipients and saves them a page at a time, from where the last run
    stopped, until the audience ends or `until` (time.monotonic()) passes; at least one page, and
    the next run goes on. A legal notice goes in each page's bell first (safe to repeat), so a
    failure in between leaves nothing missing for the next try."""
    after = send.prepared_after or ""

    while True:
        page = await audience_page(send.kind, after)
        user_ids = without_guests(page)
        done = len(page) < ID_PAGE_SIZE

        if send.kind in LEGAL_KINDS:
            await legal_in_bell(send.kind, send.about, user_ids)

        # Another run saved this page already: it goes on with the rest.
        if not await bulk_sends.save_page(
            send.id, after, page[-1] if page else after, user_ids, done
        ):
            return

        if done:
            logger.info("Bulk send %s (%s) has all its recipients", send.id, send.kind)

            return

        after = page[-1]

        if time.monotonic() > until:
            return


async def prepare_now(kind: str, about: str) -> None:
    """Right after a send starts, its first page of recipients, so its counts show at once (all of
    them for an audience of one page); the runs work out the rest. Never raises: the next run
    prepares a send this couldn't."""
    try:
        await prepare(await bulk_sends.get(kind, about), until=0)
    except Exception:
        logger.exception("Couldn't work out the recipients of %s %s yet", kind, about)


async def quota_left(sent_today: int) -> int:
    """Bulk emails that may still go out today: Resend's daily quota (RESEND_DAILY_LIMIT) less
    the share kept for everything else (RESEND_RESERVE_PERCENT)."""
    quota = await limit(get_redis(), "RESEND_DAILY_LIMIT")
    reserve = await limit(get_redis(), "RESEND_RESERVE_PERCENT")

    return max(0, int(quota * (100 - reserve) / 100) - sent_today)


def skip_reason(kind: str, person: dict | None, suppressed_hashes: set[str]) -> str | None:
    """Why this user isn't sent the email now, if they aren't."""
    if person is None:
        return SkipReason.GONE

    if address_hash(person["email"]) in suppressed_hashes:
        return SkipReason.SUPPRESSED

    if kind in CAMPAIGN_KINDS and not person["preferences"].get(kind):
        return SkipReason.UNSUBSCRIBED

    return None


async def send_one(row: tuple, person: dict | None, hashes: set[str], campaign) -> bool:
    """Sends one recipient's email (bulk_recipients.claimed); whether it went out. A failure is
    tried again in a later run, up to MAX_ATTEMPTS; one Resend refuses for good fails at once.
    Over Resend's limit, ResendBusy stops the run and the row stays pending."""
    row_id, send_id, user_id, kind, about = row

    async with bulk_recipients.claimed(row_id) as claimed:
        if claimed is None:
            return False

        reason = skip_reason(kind, person, hashes)

        if reason is None and kind in CAMPAIGN_KINDS and campaign is None:
            reason = SkipReason.STOPPED

        if reason is not None:
            claimed.status, claimed.reason = RecipientStatus.SKIPPED, reason

            return False

        email = email_for(kind, about, str(send_id), person, campaign)

        try:
            await delivery.transmit(email, f"bulk/{send_id}/{user_id}")
        except ResendBusy:
            raise
        except Exception as error:
            claimed.attempts += 1
            claimed.reason = f"{type(error).__name__}: {error}"[:MAX_REASON_LENGTH]

            if isinstance(error, EmailRefused) or claimed.attempts >= MAX_ATTEMPTS:
                claimed.status = RecipientStatus.FAILED

            logger.warning("Bulk email %s to %s failed", send_id, user_id, exc_info=True)

            return False

        claimed.status, claimed.sent_at = RecipientStatus.SENT, datetime.now(UTC)

    return True


async def send_bulk(now: datetime) -> int:
    """One run at a time (two at once would each spend the day's whole quota): a run that finds
    another still going sends nothing. Returns how many were sent."""
    redis = get_redis()
    token = await redis_lock.acquire(redis, BULK_LOCK_KEY, BULK_LOCK_SECONDS)

    if token is None:
        return 0

    try:
        return await send_run(now)
    finally:
        await redis_lock.release(redis, BULK_LOCK_KEY, token)


async def send_run(now: datetime) -> int:
    """Prepares the sends that need it (a page at a time, until its time is up), then sends the
    next pending recipients, a batch at a time, until its time is up or the day's quota is used.
    Each batch's addresses, languages and settings are read just before sending, so a changed
    address or a deleted account counts. Returns how many were sent."""
    stop = deadline()

    for send in await bulk_sends.unprepared():
        if time.monotonic() > stop:
            break

        await prepare(send, stop)

    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    left = await quota_left(await bulk_recipients.sent_since(midnight))
    sent = 0
    tried = []
    loaded = {}

    while time.monotonic() < stop and left > sent:
        batch = await bulk_recipients.pending(min(BULK_BATCH, left - sent), tried)

        if not batch:
            break

        people = {
            person["user_id"]: person
            for person in await library.recipients(list({row[2] for row in batch}))
        }
        hashes = await suppressed.among([address_hash(p["email"]) for p in people.values()])

        for row in batch:
            if time.monotonic() > stop:
                break

            tried.append(row[0])
            kind, about = row[3], row[4]

            if kind in CAMPAIGN_KINDS and about not in loaded:
                loaded[about] = await campaign_texts(about)

            if await send_one(row, people.get(row[2]), hashes, loaded.get(about)):
                sent += 1
                await asyncio.sleep(SEND_INTERVAL_SECONDS)

    if left <= sent and await bulk_recipients.pending(1, []):
        logger.warning("Bulk emails reached today's share of Resend's quota: the rest go tomorrow")
        await record_hit("RESEND_DAILY_LIMIT", what="bulk_email")

    await bulk_sends.finish_done()

    return sent
