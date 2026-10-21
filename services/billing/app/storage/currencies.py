from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert

from app.constants.currencies import ChoiceOwner
from app.models.billing import CurrencyChoice
from app.storage.db import Session


async def chosen(owner_type: ChoiceOwner, owner_id: str) -> str | None:
    async with Session() as session:
        row = await session.get(CurrencyChoice, (owner_type, owner_id))

    return row.currency if row else None


async def chosen_many(owner_type: ChoiceOwner, owner_ids: list[str]) -> dict[str, str]:
    """The currencies these owners chose, by owner; those without one are left out."""
    query = select(CurrencyChoice.owner_id, CurrencyChoice.currency).where(
        CurrencyChoice.owner_type == owner_type, CurrencyChoice.owner_id.in_(owner_ids)
    )

    async with Session() as session:
        return {row.owner_id: row.currency for row in await session.execute(query)}


async def choose(owner_type: ChoiceOwner, owner_id: str, currency: str) -> None:
    upsert = insert(CurrencyChoice).values(
        owner_type=owner_type, owner_id=owner_id, currency=currency
    )

    async with Session() as session:
        await session.execute(
            upsert.on_conflict_do_update(
                index_elements=["owner_type", "owner_id"], set_={"currency": currency}
            )
        )
        await session.commit()


async def remember(owner_type: ChoiceOwner, owner_id: str, currency: str) -> str:
    """Saves `currency` unless the owner has one already; the one saved either way. Two first
    requests at once save one."""
    upsert = insert(CurrencyChoice).values(
        owner_type=owner_type, owner_id=owner_id, currency=currency
    )

    async with Session() as session:
        await session.execute(upsert.on_conflict_do_nothing())
        await session.commit()
        row = await session.get(CurrencyChoice, (owner_type, owner_id), populate_existing=True)

    return row.currency


async def forget(owner_type: ChoiceOwner, owner_id: str) -> None:
    async with Session() as session:
        await session.execute(
            delete(CurrencyChoice).where(
                CurrencyChoice.owner_type == owner_type, CurrencyChoice.owner_id == owner_id
            )
        )
        await session.commit()
