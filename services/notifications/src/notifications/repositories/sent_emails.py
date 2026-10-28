from datetime import date, timedelta

from prepza_common.db.db import delete_in_batches
from sqlalchemy import delete, exists, func, select

from notifications.core.db import Session
from notifications.models.sent_emails import SentEmail


def day_key(day: date) -> str:
    return f"day:{day.isoformat()}"


def about_keys(items: list[str]) -> list[str]:
    return [f"about:{item}" for item in items]


async def claim(
    user_id: str, kind: str, today: date, every_days: int, items: list[str] = ()
) -> list[str] | None:
    """Claims sending the `kind` email to the user today. None when one went out within the
    last `every_days` days, or when a reminder's `items` were all named before; otherwise the
    items not named yet, now marked as named. One user's claims of a kind run one at a time,
    so two runs at once can't both claim."""
    async with Session() as session:
        await session.execute(
            select(func.pg_advisory_xact_lock(func.hashtext(f"{user_id}:{kind}")))
        )
        mine = (SentEmail.user_id == user_id, SentEmail.kind == kind)
        recent = await session.scalar(
            select(
                exists().where(
                    *mine,
                    SentEmail.key.startswith("day:"),
                    SentEmail.sent_on > today - timedelta(days=every_days),
                )
            )
        )

        if recent:
            return None

        named = set(
            await session.scalars(
                select(SentEmail.key).where(*mine, SentEmail.key.in_(about_keys(items)))
            )
        )
        new = [item for item in items if f"about:{item}" not in named]

        if items and not new:
            return None

        session.add_all(
            SentEmail(user_id=user_id, kind=kind, key=key, sent_on=today)
            for key in [day_key(today), *about_keys(new)]
        )
        await session.commit()

        return new


async def release(user_id: str, kind: str, today: date, items: list[str]) -> None:
    """Takes back a claim whose email couldn't be sent, so a later run sends it."""
    async with Session() as session:
        await session.execute(
            delete(SentEmail).where(
                SentEmail.user_id == user_id,
                SentEmail.kind == kind,
                SentEmail.key.in_([day_key(today), *about_keys(items)]),
            )
        )
        await session.commit()


async def forget(before: date, until: float | None = None) -> None:
    """Rows older than every window that reads them go, in batches, none started after `until`
    (time.monotonic()); the next run deletes the rest."""
    await delete_in_batches(Session, SentEmail, SentEmail.sent_on < before, until=until)


async def remove_user(user_id: str) -> None:
    async with Session() as session:
        await session.execute(delete(SentEmail).where(SentEmail.user_id == user_id))
        await session.commit()
