import uuid
from datetime import UTC, datetime, timedelta

from prepza_common import audit
from prepza_common.audit_actions import AuditAction, TargetKind
from prepza_common.constants import DELETED_USER
from sqlalchemy import delete, exists, select, update
from sqlalchemy.dialects.postgresql import insert

from app.constants.notifications import EXPIRED_PER_PRUNE, KEEP_DAYS
from app.constants.slack import SlackStatus
from app.models.outbox import OutboxEvent
from app.models.slack import SlackConnection, SlackPost
from app.storage.db import Session


async def get(company_id: str) -> SlackConnection | None:
    async with Session() as session:
        return await session.get(SlackConnection, company_id)


async def token_in_use(token_hash: str) -> bool:
    """Whether a company still has the workspace token of that hash (helpers/slack.py
    token_hash): companies on one workspace share it."""
    async with Session() as session:
        return bool(
            await session.scalar(select(exists().where(SlackConnection.token_hash == token_hash)))
        )


async def connect(
    company_id: str,
    team: str,
    channel: str,
    webhook: str,
    token: str,
    token_hash: str,
    kinds: list,
    user_id: str,
) -> None:
    """Saves the company's channel, replacing an earlier one; the kinds it chose stay. The
    company's action log gets it as `user_id`'s."""
    values = {
        "team": team,
        "channel": channel,
        "webhook": webhook,
        "token": token,
        "token_hash": token_hash,
        "status": SlackStatus.CONNECTED,
        "created_by": user_id,
    }
    query = (
        insert(SlackConnection)
        .values(company_id=company_id, kinds=kinds, **values)
        .on_conflict_do_update(index_elements=["company_id"], set_=values)
    )

    async with Session() as session:
        await session.execute(query)
        audit.add(
            session,
            OutboxEvent,
            company_id,
            user_id,
            AuditAction.SLACK_CONNECTED,
            TargetKind.INTEGRATION,
            target_label=channel,
        )
        await session.commit()


async def set_kinds(company_id: str, kinds: list, user_id: str) -> None:
    """The company's action log gets it as `user_id`'s, when the company has a channel."""
    query = (
        update(SlackConnection)
        .where(SlackConnection.company_id == company_id)
        .values(kinds=kinds)
        .returning(SlackConnection.channel)
    )

    async with Session() as session:
        channel = await session.scalar(query)

        if channel is not None:
            audit.add(
                session,
                OutboxEvent,
                company_id,
                user_id,
                AuditAction.SLACK_NOTIFICATIONS_CHANGED,
                TargetKind.INTEGRATION,
                target_label=channel,
            )

        await session.commit()


async def mark_broken(company_id: str) -> bool:
    """True when it stopped working just now: of several calls at once, only one."""
    query = (
        update(SlackConnection)
        .where(
            SlackConnection.company_id == company_id,
            SlackConnection.status != SlackStatus.BROKEN,
        )
        .values(status=SlackStatus.BROKEN)
        .returning(SlackConnection.company_id)
    )

    async with Session() as session:
        stopped = await session.scalar(query)
        await session.commit()

    return stopped is not None


async def made_by(user_id: str) -> list[SlackConnection]:
    query = select(SlackConnection).where(SlackConnection.created_by == user_id)

    async with Session() as session:
        return list(await session.scalars(query))


async def forget_maker(user_id: str) -> list[str]:
    """The channels the user connected stay with their companies, without the user's id, and
    stop working, as when their maker stops being an editor: an editor reconnects them. The
    companies whose channel stopped working just now."""
    working = (
        update(SlackConnection)
        .where(SlackConnection.created_by == user_id, SlackConnection.status != SlackStatus.BROKEN)
        .values(created_by=DELETED_USER, status=SlackStatus.BROKEN)
        .returning(SlackConnection.company_id)
    )
    rest = (
        update(SlackConnection)
        .where(SlackConnection.created_by == user_id)
        .values(created_by=DELETED_USER)
    )

    async with Session() as session:
        stopped = list(await session.scalars(working))
        await session.execute(rest)
        await session.commit()

    return stopped


async def remove(company_id: str, user_id: str | None = None) -> None:
    """A member's (`user_id`) goes to the company's action log."""
    query = (
        delete(SlackConnection)
        .where(SlackConnection.company_id == company_id)
        .returning(SlackConnection.channel)
    )

    async with Session() as session:
        channel = await session.scalar(query)

        if channel is not None and user_id is not None:
            audit.add(
                session,
                OutboxEvent,
                company_id,
                user_id,
                AuditAction.SLACK_DISCONNECTED,
                TargetKind.INTEGRATION,
                target_label=channel,
            )

        await session.commit()


async def connected(company_id: str) -> SlackConnection | None:
    """The company's working channel, if any. An id that can't be a company's has none, so an
    event naming one is handled instead of failing on every redelivery."""
    try:
        uuid.UUID(company_id)
    except ValueError:
        return None

    query = select(SlackConnection).where(
        SlackConnection.company_id == company_id, SlackConnection.status == SlackStatus.CONNECTED
    )

    async with Session() as session:
        return await session.scalar(query)


async def claim(key: str) -> bool:
    """Marks the notification `key` as posted to Slack; False when it already was (or is being
    posted right now), so a retried or duplicate event posts it once. Expired marks go, at most
    EXPIRED_PER_PRUNE a call, long after Pub/Sub stops redelivering (7 days)."""
    now = datetime.now(UTC)
    expired = (
        select(SlackPost.event_id)
        .where(SlackPost.posted_at < now - timedelta(days=KEEP_DAYS))
        .limit(EXPIRED_PER_PRUNE)
        .with_for_update(skip_locked=True)
    )

    async with Session() as session:
        await session.execute(delete(SlackPost).where(SlackPost.event_id.in_(expired)))
        claimed = await session.scalar(
            insert(SlackPost)
            .values(event_id=key, posted_at=now)
            .on_conflict_do_nothing(index_elements=["event_id"])
            .returning(SlackPost.event_id)
        )
        await session.commit()

    return claimed is not None


async def release(key: str) -> None:
    """Slack didn't take the notification `key`: the event's retry may post it."""
    async with Session() as session:
        await session.execute(delete(SlackPost).where(SlackPost.event_id == key))
        await session.commit()
