from datetime import date

from sqlalchemy import delete, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from testee_common.db.db import delete_in_batches

from notifications.models.sent_emails import SentEmail


def day_key(day: date) -> str:
    return f"day:{day.isoformat()}"


def about_keys(items: list[str]) -> list[str]:
    return [f"about:{item}" for item in items]


async def lock(session: AsyncSession, user_id: str, kind: str) -> None:
    """One user's claims of a kind run one at a time, so two runs at once can't both claim."""
    await session.execute(select(func.pg_advisory_xact_lock(func.hashtext(f"{user_id}:{kind}"))))


async def sent_after(session: AsyncSession, user_id: str, kind: str, after: date) -> bool:
    """Whether a `kind` email went to the user on a day after `after`."""
    return bool(
        await session.scalar(
            select(
                exists().where(
                    SentEmail.user_id == user_id,
                    SentEmail.kind == kind,
                    SentEmail.key.startswith("day:"),
                    SentEmail.sent_on > after,
                )
            )
        )
    )


async def named(session: AsyncSession, user_id: str, kind: str, items: list[str]) -> set[str]:
    """Which of the items a `kind` email named to the user before."""
    keys = await session.scalars(
        select(SentEmail.key).where(
            SentEmail.user_id == user_id,
            SentEmail.kind == kind,
            SentEmail.key.in_(about_keys(items)),
        )
    )

    return {key.removeprefix("about:") for key in keys}


async def mark(
    session: AsyncSession, user_id: str, kind: str, today: date, items: list[str]
) -> None:
    """The `kind` email to the user today, naming the items."""
    session.add_all(
        SentEmail(user_id=user_id, kind=kind, key=key, sent_on=today)
        for key in [day_key(today), *about_keys(items)]
    )
    await session.flush()


async def release(
    session: AsyncSession, user_id: str, kind: str, today: date, items: list[str]
) -> None:
    """Takes back a claim whose email couldn't be sent, so a later run sends it."""
    await session.execute(
        delete(SentEmail).where(
            SentEmail.user_id == user_id,
            SentEmail.kind == kind,
            SentEmail.key.in_([day_key(today), *about_keys(items)]),
        )
    )


async def forget(sessions, before: date, until: float | None = None) -> None:
    """Rows older than every window that reads them go, in batches (each its own transaction),
    none started after `until` (time.monotonic()); the next run deletes the rest."""
    await delete_in_batches(sessions, SentEmail, SentEmail.sent_on < before, until=until)


async def remove_user(session: AsyncSession, user_id: str) -> None:
    await session.execute(delete(SentEmail).where(SentEmail.user_id == user_id))


async def of_user(session: AsyncSession, user_id: str) -> list[SentEmail]:
    """The user's log of digests and reminders, for their export, newest first."""
    rows = await session.scalars(
        select(SentEmail)
        .where(SentEmail.user_id == user_id)
        .order_by(SentEmail.sent_on.desc(), SentEmail.id.desc())
    )

    return list(rows)
