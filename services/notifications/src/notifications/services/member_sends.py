import asyncio
import hashlib
import logging
import time
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta

from notifications.constants.member_emails import (
    LAST_RUN_MINUTE,
    RUN_SECONDS,
    SEND_INTERVAL_SECONDS,
    MemberEmail,
)
from notifications.core.db import Session
from notifications.models.email import Email
from notifications.repositories import sent_emails
from notifications.services import delivery

logger = logging.getLogger(__name__)

# One user's email: who, what it may name (empty for one that names nothing tracked), and how
# to build it from the items not named before.
Job = tuple[str, list[str], Callable[[list[str]], Email]]


def deadline() -> float:
    """When a run that starts now stops sending."""
    return time.monotonic() + RUN_SECONDS


def stopped(kind: MemberEmail) -> None:
    """The next run goes on. At an hour's last run, the rest wait for the catch-up hour, and an
    error says sending is too slow for its hour."""
    if datetime.now(UTC).minute >= LAST_RUN_MINUTE:
        logger.error(
            "The %s emails didn't all go out within their hour: sending needs speeding up", kind
        )

        return

    logger.info("Stopped sending %s emails for now; the next run goes on", kind)


async def claim(
    user_id: str, kind: str, today: date, every_days: int, items: list[str] = ()
) -> list[str] | None:
    """Claims sending the `kind` email to the user today. None when one went out within the
    last `every_days` days, or when a reminder's `items` were all named before; otherwise the
    items not named yet, now marked as named. One user's claims of a kind run one at a time
    (a lock), so two runs at once can't both claim."""
    async with Session.begin() as session:
        await sent_emails.lock(session, user_id, kind)

        if await sent_emails.sent_after(session, user_id, kind, today - timedelta(days=every_days)):
            return None

        named = await sent_emails.named(session, user_id, kind, list(items))
        new = [item for item in items if item not in named]

        if items and not new:
            return None

        await sent_emails.mark(session, user_id, kind, today, new)

    return new


async def release(user_id: str, kind: str, today: date, items: list[str]) -> None:
    """Takes back a claim whose email couldn't be sent, so a later run sends it."""
    async with Session.begin() as session:
        await sent_emails.release(session, user_id, kind, today, items)


async def send_once(
    kind: MemberEmail, today: date, every_days: int, jobs: list[Job], until: float
) -> int:
    """Sends each job's email unless one of `kind` went to that user within `every_days` days
    (or it names nothing new), paced under Resend's limit, until `until` (deadline()); the next
    run goes on with the rest. A claim is taken back when its email fails, so a later run
    sends it; over Resend's limit, ResendBusy stops the run. Returns how many were sent."""
    sent = 0

    for user_id, items, build in jobs:
        if time.monotonic() > until:
            stopped(kind)

            break

        new = await claim(user_id, kind, today, every_days, items)

        if new is None:
            continue

        email = build(new)
        # The same email again (a retry after a send that failed but went through) has the
        # same key, which Resend sends once; a different one, a key of its own.
        content = hashlib.sha256(email.text.encode()).hexdigest()[:32]

        try:
            await delivery.send(email, f"{kind}/{user_id}/{content}")
        except Exception:
            await release(user_id, kind, today, new)

            raise

        sent += 1
        await asyncio.sleep(SEND_INTERVAL_SECONDS)

    return sent
