from datetime import UTC, datetime

from prepza_common.config.constants import GUEST_UID_PREFIX
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from accounts.constants.emails import (
    CONSENT_TEXT_VERSION,
    DEFAULTS,
    ConsentBasis,
    ConsentSource,
    EmailSetting,
)
from accounts.models.emails import EmailConsent, EmailPreferences


def as_dict(row: EmailPreferences | None) -> dict[str, bool]:
    if row is None:
        return dict(DEFAULTS)

    return {setting: getattr(row, setting) for setting in EmailSetting}


async def preferences(session: AsyncSession, user_id: str) -> dict[str, bool]:
    return as_dict(await session.get(EmailPreferences, user_id))


async def preferences_of(session: AsyncSession, user_ids: list[str]) -> dict[str, dict[str, bool]]:
    """Several users' preferences at once, by id."""
    query = select(EmailPreferences).where(EmailPreferences.user_id.in_(user_ids))

    found = {row.user_id: row for row in await session.scalars(query)}

    return {user_id: as_dict(found.get(user_id)) for user_id in user_ids}


async def ids_with(
    session: AsyncSession, setting: EmailSetting, after: str, limit: int
) -> list[str]:
    """The users who have the setting on, never a company's guest candidate, in order: up to
    `limit` after `after`. Only users with stored preferences: product updates and offers are
    off by default."""
    query = (
        select(EmailPreferences.user_id)
        .where(
            getattr(EmailPreferences, setting).is_(True),
            EmailPreferences.user_id.not_like(f"{GUEST_UID_PREFIX}%"),
            EmailPreferences.user_id > after,
        )
        .order_by(EmailPreferences.user_id)
        .limit(limit)
    )

    return list(await session.scalars(query))


async def having(session: AsyncSession, setting: EmailSetting, user_ids: list[str]) -> list[str]:
    """Those of the users who have the setting on, in the order given."""
    query = select(EmailPreferences.user_id).where(
        EmailPreferences.user_id.in_(user_ids), getattr(EmailPreferences, setting).is_(True)
    )

    found = set(await session.scalars(query))

    return [user_id for user_id in user_ids if user_id in found]


async def lock(session: AsyncSession, user_id: str) -> tuple[EmailPreferences, bool]:
    """The user's preferences, made with the defaults when there are none, locked, so concurrent
    changes don't miss each other; and whether they were made now."""
    created = await session.scalar(
        insert(EmailPreferences)
        .values(user_id=user_id)
        .on_conflict_do_nothing()
        .returning(EmailPreferences.user_id)
    )

    return await session.get(EmailPreferences, user_id, with_for_update=True), created is not None


def apply(
    session: AsyncSession,
    row: EmailPreferences,
    changes: list[tuple[EmailSetting, bool, ConsentBasis]],
    source: ConsentSource,
    changed_by: str | None = None,
) -> dict[str, bool]:
    """Saves each change with its line in the consent log; the preferences as they now are.
    `changed_by` is the superadmin, for the admin source."""
    for setting, on, basis in changes:
        setattr(row, setting, on)
        row.updated_at = datetime.now(UTC)
        session.add(
            EmailConsent(
                user_id=row.user_id,
                setting=setting,
                granted=on,
                source=source,
                basis=basis,
                text_version=CONSENT_TEXT_VERSION,
                changed_by=changed_by,
            )
        )

    return as_dict(row)


async def consents(session: AsyncSession, user_id: str) -> list[dict]:
    """The user's consent log, oldest first."""
    query = (
        select(EmailConsent)
        .where(EmailConsent.user_id == user_id)
        .order_by(EmailConsent.created_at, EmailConsent.id)
    )

    rows = (await session.scalars(query)).all()

    return [
        {
            "setting": row.setting,
            "granted": row.granted,
            "source": row.source,
            "basis": row.basis,
            "text_version": row.text_version,
            "at": row.created_at,
        }
        for row in rows
    ]
