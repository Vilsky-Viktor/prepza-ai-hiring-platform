from datetime import datetime, timedelta

from prepza_common.events.notifications import NotificationKind, Recipient
from sqlalchemy import and_, delete, func, or_, select, tuple_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from notifications.constants.member_emails import INTERVIEW_LINK
from notifications.constants.notifications import (
    EXPIRED_PER_PRUNE,
    GROUP_HOURS,
    KEEP_DAYS,
    MAX_PER_RECIPIENT,
)
from notifications.models.notifications import Notification, Received, Seen

# (recipient, recipient_id): a user's own notifications and their companies'.
Recipients = list[tuple[str, str]]


def for_recipients(recipients: Recipients, since: datetime | None = None):
    """The recipients' notifications, and with `since` (when the user's account was made) the
    notifications for everyone that came after it. A user's items about a company's notes show
    only while they're a member of it (among the recipients)."""
    company_ids = [id_ for kind, id_ in recipients if kind == Recipient.COMPANY]
    own = and_(
        tuple_(Notification.recipient, Notification.recipient_id).in_(recipients),
        or_(
            Notification.kind != NotificationKind.NOTE_ADDED,
            Notification.data["company_id"].astext.in_(company_ids),
        ),
    )

    if since is None:
        return own

    return or_(own, and_(Notification.recipient == Recipient.ALL, Notification.created_at > since))


async def lock_recipient(session: AsyncSession, recipient: str) -> None:
    """One recipient's notifications are stored one at a time, though Pub/Sub delivers in
    parallel, so a burst still groups and the limit holds; other recipients don't wait.
    `recipient` is "<recipient>:<recipient_id>"."""
    await session.execute(select(func.pg_advisory_xact_lock(func.hashtext(recipient))))


async def is_deleted(session: AsyncSession, recipient: str) -> bool:
    """Whether the recipient is a deleted company (remove_company)."""
    return await has_received(session, deleted_key(recipient))


async def has_received(session: AsyncSession, event_id: str) -> bool:
    """Whether `event_id` (an event's, a producer's key or a mark) came."""
    return await session.get(Received, event_id) is not None


async def claim(session: AsyncSession, event_id: str, now: datetime) -> bool:
    """Marks `event_id` (the event's, or the producer's `key`) as received; False when it already
    was, however often it comes."""
    first = await session.scalar(
        insert(Received)
        .values(event_id=event_id, received_at=now)
        .on_conflict_do_nothing(index_elements=["event_id"])
        .returning(Received.event_id)
    )

    return first is not None


async def add(session: AsyncSession, event_id: str, event: dict, now: datetime) -> None:
    """A new notification."""
    session.add(
        Notification(
            event_id=event_id,
            recipient=event["recipient"],
            recipient_id=event["recipient_id"],
            kind=event["kind"],
            link=event["link"],
            data=event.get("data") or {},
            created_at=now,
        )
    )
    await session.flush()


async def add_to_group(session: AsyncSession, event: dict, now: datetime) -> bool:
    """Adds the event to the recipient's latest notification of its kind about the same page and
    title, if it came within GROUP_HOURS: one more in its count, the newest details, and back at
    the top as unread. False when there's none to add to."""
    data = event.get("data") or {}
    title = Notification.data["title"].astext
    group = await session.scalar(
        select(Notification)
        .where(
            Notification.recipient == event["recipient"],
            Notification.recipient_id == event["recipient_id"],
            Notification.kind == event["kind"],
            Notification.link == event["link"],
            title == data["title"] if "title" in data else title.is_(None),
            Notification.created_at > now - timedelta(hours=GROUP_HOURS),
        )
        .order_by(Notification.created_at.desc())
        .limit(1)
        .with_for_update()
    )

    if group is None:
        return False

    group.data = {**data, "count": group.data.get("count", 1) + 1}
    group.created_at = now

    return True


async def prune(session: AsyncSession, event: dict, now: datetime) -> None:
    """The recipient keeps their newest MAX_PER_RECIPIENT; nothing is kept past KEEP_DAYS. Each
    call removes at most EXPIRED_PER_PRUNE expired rows of each table, skipping rows another
    call is removing, so it stays quick and never waits."""
    oldest_kept = now - timedelta(days=KEEP_DAYS)
    beyond_limit = (
        select(Notification.id)
        .where(
            Notification.recipient == event["recipient"],
            Notification.recipient_id == event["recipient_id"],
        )
        .order_by(Notification.created_at.desc())
        .offset(MAX_PER_RECIPIENT)
    )
    expired = (
        select(Notification.id)
        .where(Notification.created_at < oldest_kept)
        .limit(EXPIRED_PER_PRUNE)
        .with_for_update(skip_locked=True)
    )
    expired_events = (
        select(Received.event_id)
        .where(Received.received_at < oldest_kept)
        .limit(EXPIRED_PER_PRUNE)
        .with_for_update(skip_locked=True)
    )
    await session.execute(delete(Notification).where(Notification.id.in_(beyond_limit)))
    await session.execute(delete(Notification).where(Notification.id.in_(expired)))
    await session.execute(delete(Received).where(Received.event_id.in_(expired_events)))


async def latest(
    session: AsyncSession, recipients: Recipients, limit: int | None, since: datetime | None = None
) -> list[Notification]:
    """Newest first; all of them when `limit` is None. With `since`, everyone's too."""
    rows = await session.scalars(
        select(Notification)
        .where(for_recipients(recipients, since))
        .order_by(Notification.created_at.desc())
        .limit(limit)
    )

    return list(rows)


async def unread_count(
    session: AsyncSession, recipients: Recipients, user_id: str, since: datetime | None = None
) -> int:
    """Everything newer than when the user last opened the bell."""
    seen_at = await session.scalar(select(Seen.seen_at).where(Seen.user_id == user_id))
    query = select(func.count()).select_from(Notification).where(for_recipients(recipients, since))

    if seen_at is not None:
        query = query.where(Notification.created_at > seen_at)

    return await session.scalar(query) or 0


async def seen_at(session: AsyncSession, user_id: str) -> datetime | None:
    """When the user last opened the bell."""
    return await session.scalar(select(Seen.seen_at).where(Seen.user_id == user_id))


async def mark_seen(session: AsyncSession, user_id: str, now: datetime) -> None:
    await session.execute(
        insert(Seen)
        .values(user_id=user_id, seen_at=now)
        .on_conflict_do_update(index_elements=["user_id"], set_={"seen_at": now})
    )


async def remove_user(session: AsyncSession, user_id: str) -> None:
    """A deleted account takes its notifications and its seen time with it."""
    await session.execute(
        delete(Notification).where(
            Notification.recipient == Recipient.USER, Notification.recipient_id == user_id
        )
    )
    await session.execute(delete(Seen).where(Seen.user_id == user_id))


async def remove_candidate(
    session: AsyncSession, email: str, company_id: str | None = None
) -> None:
    """Company notifications about the candidate with this email go: one company's when it erased
    them, every company's when they deleted their account. Safe to repeat."""
    query = delete(Notification).where(
        Notification.recipient == Recipient.COMPANY,
        Notification.data["email"].astext == email.lower(),
    )

    if company_id is not None:
        query = query.where(Notification.recipient_id == company_id)

    await session.execute(query)


async def remove_interview_candidates(
    session: AsyncSession, company_id: str, interview_id: str
) -> None:
    """A deleted interview's candidates: the company's notifications about them (their email,
    name and grade; those opening the interview's pages) go. Its other notifications (ready,
    cancelled) name only the interview and stay. Safe to repeat."""
    link = INTERVIEW_LINK.format(company_id=company_id, interview_id=interview_id)
    await session.execute(
        delete(Notification).where(
            Notification.recipient == Recipient.COMPANY,
            Notification.recipient_id == company_id,
            Notification.link.startswith(link, autoescape=True),
            Notification.data.has_key("email"),
        )
    )


async def remove_member(session: AsyncSession, email: str) -> None:
    """An owner's notifications that this person joined their company go with the person's
    account. Safe to repeat."""
    await session.execute(
        delete(Notification).where(
            Notification.kind == NotificationKind.MEMBER_JOINED,
            Notification.data["email"].astext == email.lower(),
        )
    )


def deleted_key(recipient: str) -> str:
    """The Received row that marks a recipient as deleted; it's pruned with the others after
    KEEP_DAYS, long after Pub/Sub stops redelivering (7 days)."""
    return f"deleted:{recipient}"


async def remove_company(session: AsyncSession, company_id: str, now: datetime) -> None:
    """A deleted company takes its notifications with it, and gets none after. Safe to repeat."""
    recipient = f"{Recipient.COMPANY}:{company_id}"
    # The same lock as storing one, so a notification being stored now is removed too.
    await lock_recipient(session, recipient)
    await session.execute(
        delete(Notification).where(
            Notification.recipient == Recipient.COMPANY,
            Notification.recipient_id == company_id,
        )
    )
    await session.execute(
        insert(Received)
        .values(event_id=deleted_key(recipient), received_at=now)
        .on_conflict_do_nothing(index_elements=["event_id"])
    )


async def remove_news(session: AsyncSession, news_id: str) -> None:
    """A deleted news post's notification goes. Safe to repeat."""
    await session.execute(
        delete(Notification).where(
            Notification.recipient == Recipient.ALL,
            Notification.kind == NotificationKind.NEWS,
            Notification.data["news_id"].astext == news_id,
        )
    )
