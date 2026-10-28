from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert

from notifications.core.db import Session
from notifications.models.suppressed import SuppressedAddress


async def add(address: str, reason: str) -> None:
    """`address` is its hash. The first reason stays; safe to repeat."""
    async with Session() as session:
        await session.execute(
            insert(SuppressedAddress)
            .values(address=address, reason=reason)
            .on_conflict_do_nothing()
        )
        await session.commit()


async def among(addresses: list[str]) -> set[str]:
    """Which of these address hashes are suppressed."""
    async with Session() as session:
        found = await session.scalars(
            select(SuppressedAddress.address).where(SuppressedAddress.address.in_(addresses))
        )

        return set(found)


async def get(address: str) -> SuppressedAddress | None:
    async with Session() as session:
        return await session.get(SuppressedAddress, address)


async def remove(address: str) -> None:
    async with Session() as session:
        await session.execute(delete(SuppressedAddress).where(SuppressedAddress.address == address))
        await session.commit()
