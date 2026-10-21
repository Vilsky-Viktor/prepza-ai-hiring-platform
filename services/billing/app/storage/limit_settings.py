"""The limits superadmins changed, and every change."""

from sqlalchemy import delete, func, select

from app.models.limits import LimitChange, LimitSetting
from app.storage.db import Session


async def values() -> dict[str, float]:
    async with Session() as session:
        return {row.name: row.value for row in await session.scalars(select(LimitSetting))}


async def change(name: str, value: float | None, user_id: str, email: str) -> None:
    """Sets the limit to `value`, or back to its default (None), and keeps the change. Locked by
    its name (a row lock can't hold a limit that has no row yet), so two changes at once each
    keep their own old value."""
    async with Session() as session:
        await session.execute(select(func.pg_advisory_xact_lock(func.hashtext(f"limit:{name}"))))
        found = await session.get(LimitSetting, name, with_for_update=True)
        old = found.value if found else None

        if value is None:
            await session.execute(delete(LimitSetting).where(LimitSetting.name == name))
        elif found:
            found.value = value
        else:
            session.add(LimitSetting(name=name, value=value))

        if old != value:
            kept = {"changed_by": user_id, "changed_by_email": email}
            session.add(LimitChange(name=name, old_value=old, new_value=value, **kept))

        await session.commit()


async def changes(count: int) -> list[LimitChange]:
    query = select(LimitChange).order_by(LimitChange.changed_at.desc()).limit(count)

    async with Session() as session:
        return list(await session.scalars(query))
