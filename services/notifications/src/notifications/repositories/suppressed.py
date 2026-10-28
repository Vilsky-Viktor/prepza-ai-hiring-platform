from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from notifications.models.suppressed import SuppressedAddress


async def add(session: AsyncSession, address: str, reason: str) -> None:
    """`address` is its hash. The first reason stays; safe to repeat."""
    await session.execute(
        insert(SuppressedAddress).values(address=address, reason=reason).on_conflict_do_nothing()
    )


async def among(session: AsyncSession, addresses: list[str]) -> set[str]:
    """Which of these address hashes are suppressed."""
    found = await session.scalars(
        select(SuppressedAddress.address).where(SuppressedAddress.address.in_(addresses))
    )

    return set(found)


async def get(session: AsyncSession, address: str) -> SuppressedAddress | None:
    return await session.get(SuppressedAddress, address)


async def remove(session: AsyncSession, address: str) -> None:
    await session.execute(delete(SuppressedAddress).where(SuppressedAddress.address == address))
