from uuid import UUID

from prepza_common.config.constants import DELETED_USER
from prepza_common.events import audit, outbox
from prepza_common.events.audit_actions import AuditAction, TargetKind
from prepza_common.events.notifications import NOTIFICATION_REQUESTED
from sqlalchemy import delete, func, literal_column, select, update
from sqlalchemy.dialects.postgresql import insert

from ats.constants.ats import ATS_NAMES, ConnectionStatus
from ats.core.db import Session
from ats.helpers.notifications import connection_broken
from ats.models.ats import AtsConnection
from ats.models.outbox import OutboxEvent


def company_of(connection_id: UUID):
    """The connection's company, read by the statement that saves a row of it."""
    return (
        select(AtsConnection.company_id).where(AtsConnection.id == connection_id).scalar_subquery()
    )


async def connections(company_id: UUID) -> list[AtsConnection]:
    query = select(AtsConnection).where(AtsConnection.company_id == company_id)

    async with Session() as session:
        return list((await session.scalars(query)).all())


async def connection(company_id: UUID, provider: str) -> AtsConnection | None:
    query = select(AtsConnection).where(
        AtsConnection.company_id == company_id, AtsConnection.provider == provider
    )

    async with Session() as session:
        return await session.scalar(query)


async def connection_by_id(connection_id: UUID) -> AtsConnection | None:
    async with Session() as session:
        return await session.get(AtsConnection, connection_id)


async def connections_by_ids(connection_ids: set[UUID]) -> dict[UUID, AtsConnection]:
    query = select(AtsConnection).where(AtsConnection.id.in_(connection_ids))

    async with Session() as session:
        return {connection.id: connection for connection in await session.scalars(query)}


async def connect(
    company_id: UUID,
    provider: str,
    account: str,
    credentials: str,
    user_id: str,
    member_id: str | None = None,
    language: str | None = None,
) -> None:
    """Saves the company's connection to `provider`, replacing an earlier one's key (a
    reconnect keeps its linked jobs), with the connecting member's interface `language`; the
    company's action log gets it as theirs."""
    values = {
        "language": language,
        "account": account,
        "credentials": credentials,
        "status": ConnectionStatus.CONNECTED,
        "created_by": user_id,
        "member_id": member_id,
        # A new key may write: a refusal tells the company again.
        "write_refused_at": None,
    }
    query = (
        insert(AtsConnection)
        .values(company_id=company_id, provider=provider, **values)
        .on_conflict_do_update(index_elements=["company_id", "provider"], set_=values)
        # A row the insert made has no xmax; one it updated has: told by the same statement, so
        # two connects at once log one connect and one reconnect.
        .returning(literal_column("xmax = 0"))
    )

    async with Session() as session:
        inserted = await session.scalar(query)
        action = AuditAction.ATS_CONNECTED if inserted else AuditAction.ATS_RECONNECTED
        audit.add(
            session,
            OutboxEvent,
            company_id,
            user_id,
            action,
            TargetKind.INTEGRATION,
            target_label=ATS_NAMES[provider],
        )
        await session.commit()


async def refuse_writes(connection_id: UUID, notice: dict) -> None:
    """The ATS refused the results written back while the key still reads: `notice` tells the
    company, once, however many results are refused, and also when two at once are."""
    query = (
        update(AtsConnection)
        .where(AtsConnection.id == connection_id, AtsConnection.write_refused_at.is_(None))
        .values(write_refused_at=func.now())
        .returning(AtsConnection.id)
    )

    async with Session() as session:
        if await session.scalar(query) is not None:
            outbox.add(session, OutboxEvent, NOTIFICATION_REQUESTED, notice)

        await session.commit()


async def writes_again(connection_id: UUID) -> None:
    """A write went through (the key got write access in the ATS): a later refusal tells the
    company again."""
    async with Session() as session:
        await session.execute(
            update(AtsConnection)
            .where(AtsConnection.id == connection_id)
            .values(write_refused_at=None)
        )
        await session.commit()


async def set_credentials(connection_id: UUID, credentials: str) -> None:
    """Replaces the connection's sealed credentials (a web hook's signature key added)."""
    query = (
        update(AtsConnection)
        .where(AtsConnection.id == connection_id)
        .values(credentials=credentials)
    )

    async with Session() as session:
        await session.execute(query)
        await session.commit()


async def restore_broken(earlier: AtsConnection) -> None:
    """Puts back a connection as it was before a reconnect that failed (its key, account, maker
    and member), marked for reconnecting: its linked jobs and candidates stay."""
    query = (
        update(AtsConnection)
        .where(AtsConnection.id == earlier.id)
        .values(
            account=earlier.account,
            credentials=earlier.credentials,
            created_by=earlier.created_by,
            member_id=earlier.member_id,
            status=ConnectionStatus.BROKEN,
        )
    )

    async with Session() as session:
        await session.execute(query)
        await session.commit()


async def mark_broken(connection_id: UUID) -> None:
    """Marks the connection for reconnecting; the company is told when it stops working, once,
    also when several calls find it broken at the same moment."""
    query = (
        update(AtsConnection)
        .where(
            AtsConnection.id == connection_id,
            AtsConnection.status != ConnectionStatus.BROKEN,
        )
        .values(status=ConnectionStatus.BROKEN)
        .returning(AtsConnection.company_id, AtsConnection.provider)
    )

    async with Session() as session:
        for company_id, provider in await session.execute(query):
            outbox.add(
                session,
                OutboxEvent,
                NOTIFICATION_REQUESTED,
                connection_broken(company_id, provider),
            )

        await session.commit()


async def made_by(user_id: str) -> list[AtsConnection]:
    query = select(AtsConnection).where(AtsConnection.created_by == user_id)

    async with Session() as session:
        return list(await session.scalars(query))


async def forget_maker(user_id: str) -> None:
    """The connections the user made stay with their companies, without the user's id, and
    stop inviting, as when their maker stops being an editor: an editor reconnects them."""
    working = (
        update(AtsConnection)
        .where(
            AtsConnection.created_by == user_id,
            AtsConnection.status != ConnectionStatus.BROKEN,
        )
        .values(created_by=DELETED_USER, status=ConnectionStatus.BROKEN)
        .returning(AtsConnection.company_id, AtsConnection.provider)
    )
    rest = (
        update(AtsConnection)
        .where(AtsConnection.created_by == user_id)
        .values(created_by=DELETED_USER)
    )

    async with Session() as session:
        # Each company whose connection stops working now is told.
        for company_id, provider in await session.execute(working):
            outbox.add(
                session,
                OutboxEvent,
                NOTIFICATION_REQUESTED,
                connection_broken(company_id, provider),
            )

        await session.execute(rest)
        await session.commit()


async def disconnect(company_id: UUID, provider: str, user_id: str) -> None:
    """Deletes the connection and its key at once; its linked jobs go with it. The company's
    action log gets it as the member's (`user_id`)."""
    query = (
        delete(AtsConnection)
        .where(AtsConnection.company_id == company_id, AtsConnection.provider == provider)
        .returning(AtsConnection.id)
    )

    async with Session() as session:
        removed = await session.scalar(query)

        if removed is not None:
            audit.add(
                session,
                OutboxEvent,
                company_id,
                user_id,
                AuditAction.ATS_DISCONNECTED,
                TargetKind.INTEGRATION,
                target_label=ATS_NAMES[provider],
            )

        await session.commit()


async def delete_company(company_id: UUID) -> None:
    """A company was deleted: its connections go, with their linked jobs and candidates."""
    async with Session() as session:
        await session.execute(delete(AtsConnection).where(AtsConnection.company_id == company_id))
        await session.commit()
