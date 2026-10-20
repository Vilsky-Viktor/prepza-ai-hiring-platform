from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, exists, func, or_, select, update
from sqlalchemy.dialects.postgresql import insert

from app.constants.mcp import LAST_USED_EVERY_SECONDS
from app.models.oauth import McpGrant, OAuthClient
from app.storage.db import Session


async def save_client(client_id: str, info: dict) -> None:
    async with Session() as session:
        await session.execute(
            insert(OAuthClient).values(client_id=client_id, info=info).on_conflict_do_nothing()
        )
        await session.commit()


async def get_client(client_id: str) -> dict | None:
    async with Session() as session:
        return await session.scalar(
            select(OAuthClient.info).where(OAuthClient.client_id == client_id)
        )


async def read_document(client_id: str) -> tuple[dict, datetime] | None:
    """A metadata document app's kept copy and when it was read."""
    async with Session() as session:
        found = await session.execute(
            select(OAuthClient.info, OAuthClient.created_at).where(
                OAuthClient.client_id == client_id
            )
        )
        row = found.first()

        return (row.info, row.created_at) if row else None


async def keep_document(client_id: str, info: dict, read_at: datetime) -> None:
    """A metadata document app's copy, as just read; it replaces the one kept (its connections
    stay)."""
    async with Session() as session:
        values = {"client_id": client_id, "info": info, "created_at": read_at}
        await session.execute(
            insert(OAuthClient)
            .values(**values)
            .on_conflict_do_update(
                index_elements=[OAuthClient.client_id],
                set_={"info": info, "created_at": read_at},
            )
        )
        await session.commit()


async def add_grant(grant: McpGrant) -> McpGrant:
    async with Session() as session:
        session.add(grant)
        await session.commit()

        return grant


async def by_access(access_hash: str) -> McpGrant | None:
    async with Session() as session:
        return await session.scalar(select(McpGrant).where(McpGrant.access_hash == access_hash))


async def by_refresh(refresh_hash: str) -> McpGrant | None:
    async with Session() as session:
        return await session.scalar(select(McpGrant).where(McpGrant.refresh_hash == refresh_hash))


async def by_previous_refresh(refresh_hash: str) -> McpGrant | None:
    """The connection whose last refresh replaced this refresh token."""
    async with Session() as session:
        return await session.scalar(
            select(McpGrant).where(McpGrant.previous_refresh_hash == refresh_hash)
        )


async def rotate(grant_id: UUID, refresh_hash: str, values: dict) -> bool:
    """New tokens for the connection, only while `refresh_hash` is still its refresh token: of
    two refreshes with the same token, one gets them, the other nothing (False)."""
    query = (
        update(McpGrant)
        .where(McpGrant.id == grant_id, McpGrant.refresh_hash == refresh_hash)
        .values(**values, previous_refresh_hash=refresh_hash, refreshed_at=func.now())
    )

    async with Session() as session:
        result = await session.execute(query)
        await session.commit()

        return result.rowcount == 1


async def used(grant_id: UUID, now: datetime) -> None:
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

    async with Session() as session:
        await session.execute(query)
        await session.commit()


async def of_user(user_id: str) -> list[McpGrant]:
    """The user's connections, the latest first."""
    query = (
        select(McpGrant)
        .where(McpGrant.user_id == user_id)
        .order_by(McpGrant.created_at.desc(), McpGrant.id)
    )

    async with Session() as session:
        return list(await session.scalars(query))


async def remove(grant_id: UUID, user_id: str | None = None) -> McpGrant | None:
    """Deletes the connection (only the user's, when one is given); what was deleted, or None."""
    query = delete(McpGrant).where(McpGrant.id == grant_id)

    if user_id is not None:
        query = query.where(McpGrant.user_id == user_id)

    async with Session() as session:
        found = await session.scalar(query.returning(McpGrant))
        await session.commit()

        return found


async def delete_user(user_id: str) -> None:
    """Every connection of the user's (deleting their account). Safe to repeat."""
    async with Session() as session:
        await session.execute(delete(McpGrant).where(McpGrant.user_id == user_id))
        await session.commit()


async def delete_expired(now: datetime, idle_before: datetime) -> tuple[int, int]:
    """Connections whose refresh token expired, then apps registered before `idle_before` that
    have no connection: how many of each went."""
    no_grant = ~exists().where(McpGrant.client_id == OAuthClient.client_id)

    async with Session() as session:
        grants = await session.execute(delete(McpGrant).where(McpGrant.refresh_expires_at < now))
        clients = await session.execute(
            delete(OAuthClient).where(OAuthClient.created_at < idle_before, no_grant)
        )
        await session.commit()

        return grants.rowcount, clients.rowcount
