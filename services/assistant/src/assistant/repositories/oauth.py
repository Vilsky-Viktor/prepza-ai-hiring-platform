from datetime import datetime, timedelta
from uuid import UUID

from prepza_common.db.db import delete_in_batches
from sqlalchemy import delete, exists, func, or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from assistant.constants.mcp import LAST_USED_EVERY_SECONDS
from assistant.models.oauth import McpGrant, OAuthClient


async def save_client(session: AsyncSession, client_id: str, info: dict) -> None:
    await session.execute(
        insert(OAuthClient).values(client_id=client_id, info=info).on_conflict_do_nothing()
    )


async def get_client(session: AsyncSession, client_id: str) -> dict | None:
    return await session.scalar(select(OAuthClient.info).where(OAuthClient.client_id == client_id))


async def read_document(session: AsyncSession, client_id: str) -> tuple[dict, datetime] | None:
    """A metadata document app's kept copy and when it was read."""
    found = await session.execute(
        select(OAuthClient.info, OAuthClient.created_at).where(OAuthClient.client_id == client_id)
    )
    row = found.first()

    return (row.info, row.created_at) if row else None


async def keep_document(
    session: AsyncSession, client_id: str, info: dict, read_at: datetime
) -> None:
    """A metadata document app's copy, as just read; it replaces the one kept (its connections
    stay)."""
    values = {"client_id": client_id, "info": info, "created_at": read_at}
    await session.execute(
        insert(OAuthClient)
        .values(**values)
        .on_conflict_do_update(
            index_elements=[OAuthClient.client_id],
            set_={"info": info, "created_at": read_at},
        )
    )


async def add_grant(session: AsyncSession, grant: McpGrant) -> McpGrant:
    session.add(grant)
    await session.flush()

    return grant


async def by_access(session: AsyncSession, access_hash: str) -> McpGrant | None:
    return await session.scalar(select(McpGrant).where(McpGrant.access_hash == access_hash))


async def by_refresh(session: AsyncSession, refresh_hash: str) -> McpGrant | None:
    return await session.scalar(select(McpGrant).where(McpGrant.refresh_hash == refresh_hash))


async def by_previous_refresh(session: AsyncSession, refresh_hash: str) -> McpGrant | None:
    """The connection whose last refresh replaced this refresh token."""
    return await session.scalar(
        select(McpGrant).where(McpGrant.previous_refresh_hash == refresh_hash)
    )


async def rotate(session: AsyncSession, grant_id: UUID, refresh_hash: str, values: dict) -> bool:
    """New tokens for the connection, only while `refresh_hash` is still its refresh token: of
    two refreshes with the same token, one gets them, the other nothing (False)."""
    query = (
        update(McpGrant)
        .where(McpGrant.id == grant_id, McpGrant.refresh_hash == refresh_hash)
        .values(**values, previous_refresh_hash=refresh_hash, refreshed_at=func.now())
    )

    result = await session.execute(query)

    return result.rowcount == 1


async def used(session: AsyncSession, grant_id: UUID, now: datetime) -> None:
    """Writes when the connection was last used, at most once in LAST_USED_EVERY_SECONDS."""
    every = timedelta(seconds=LAST_USED_EVERY_SECONDS)
    query = (
        update(McpGrant)
        .where(
            McpGrant.id == grant_id,
            or_(McpGrant.last_used_at.is_(None), McpGrant.last_used_at < now - every),
        )
        .values(last_used_at=now)
    )

    await session.execute(query)


async def of_user(session: AsyncSession, user_id: str) -> list[McpGrant]:
    """The user's connections, the latest first."""
    query = (
        select(McpGrant)
        .where(McpGrant.user_id == user_id)
        .order_by(McpGrant.created_at.desc(), McpGrant.id)
    )

    return list(await session.scalars(query))


async def remove(
    session: AsyncSession, grant_id: UUID, user_id: str | None = None
) -> McpGrant | None:
    """Deletes the connection (only the user's, when one is given); what was deleted, or None."""
    query = delete(McpGrant).where(McpGrant.id == grant_id)

    if user_id is not None:
        query = query.where(McpGrant.user_id == user_id)

    return await session.scalar(query.returning(McpGrant))


async def delete_user(session: AsyncSession, user_id: str) -> None:
    """Every connection of the user's (deleting their account). Safe to repeat."""
    await session.execute(delete(McpGrant).where(McpGrant.user_id == user_id))


async def delete_expired(
    sessions: async_sessionmaker, now: datetime, idle_before: datetime
) -> tuple[int, int]:
    """Connections whose refresh token expired, then apps registered before `idle_before` that
    have no connection: how many of each went, in batches (delete_in_batches)."""
    no_grant = ~exists().where(McpGrant.client_id == OAuthClient.client_id)
    grants = await delete_in_batches(sessions, McpGrant, McpGrant.refresh_expires_at < now)
    clients = await delete_in_batches(
        sessions, OAuthClient, OAuthClient.created_at < idle_before, no_grant
    )

    return grants, clients
