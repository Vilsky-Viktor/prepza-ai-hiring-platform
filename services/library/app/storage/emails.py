from datetime import UTC, datetime

from prepza_common.config.constants import GUEST_UID_PREFIX
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.constants.emails import (
    CONSENT_TEXT_VERSION,
    DEFAULTS,
    ConsentBasis,
    ConsentSource,
    EmailSetting,
)
from app.models.emails import EmailConsent, EmailPreferences
from app.storage.db import Session


def as_dict(row: EmailPreferences | None) -> dict[str, bool]:
    if row is None:
        return dict(DEFAULTS)

    return {setting: getattr(row, setting) for setting in EmailSetting}


async def preferences(user_id: str) -> dict[str, bool]:
    async with Session() as session:
        return as_dict(await session.get(EmailPreferences, user_id))


async def preferences_of(user_ids: list[str]) -> dict[str, dict[str, bool]]:
    """Several users' preferences at once, by id."""
    query = select(EmailPreferences).where(EmailPreferences.user_id.in_(user_ids))

    async with Session() as session:
        found = {row.user_id: row for row in await session.scalars(query)}

    return {user_id: as_dict(found.get(user_id)) for user_id in user_ids}


async def ids_with(setting: EmailSetting, after: str, limit: int) -> list[str]:
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

    async with Session() as session:
        return list(await session.scalars(query))


async def having(setting: EmailSetting, user_ids: list[str]) -> list[str]:
    """Those of the users who have the setting on, in the order given."""
    query = select(EmailPreferences.user_id).where(
        EmailPreferences.user_id.in_(user_ids), getattr(EmailPreferences, setting).is_(True)
    )

    async with Session() as session:
        found = set(await session.scalars(query))

    return [user_id for user_id in user_ids if user_id in found]


async def change(
    user_id: str,
    changes: dict[EmailSetting, bool],
    source: ConsentSource,
    changed_by: str | None = None,
) -> dict[str, bool]:
    """Applies the changes and logs each one that changes something, so a repeated request
    logs nothing twice. The row is locked, so concurrent changes don't miss each other.
    `changed_by` is the superadmin, for the admin source.

    A sign-in turns updates on only for a user without a row yet, the first time they see the
    opt-out: it never turns them back on for someone who turned them off."""
    async with Session() as session:
        created = await session.scalar(
            insert(EmailPreferences)
            .values(user_id=user_id)
            .on_conflict_do_nothing()
            .returning(EmailPreferences.user_id)
        )
        row = await session.get(EmailPreferences, user_id, with_for_update=True)

        for setting, on in changes.items():
            soft_opt_in = source == ConsentSource.SIGN_IN and setting == EmailSetting.UPDATES and on

            if getattr(row, setting) == on or (soft_opt_in and created is None):
                continue

            setattr(row, setting, on)
            row.updated_at = datetime.now(UTC)
            session.add(
                EmailConsent(
                    user_id=user_id,
                    setting=setting,
                    granted=on,
                    source=source,
                    basis=ConsentBasis.SOFT_OPT_IN if soft_opt_in else ConsentBasis.CHOICE,
                    text_version=CONSENT_TEXT_VERSION,
                    changed_by=changed_by,
                )
            )

        await session.commit()

        return as_dict(row)


async def consents(user_id: str) -> list[dict]:
    """The user's consent log, oldest first."""
    query = (
        select(EmailConsent)
        .where(EmailConsent.user_id == user_id)
        .order_by(EmailConsent.created_at, EmailConsent.id)
    )

    async with Session() as session:
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
