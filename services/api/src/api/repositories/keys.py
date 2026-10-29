import uuid
from datetime import UTC, datetime

from prepza_common.events import audit
from prepza_common.events.audit_actions import AuditAction, TargetKind
from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.constants.api import LAST_USED_EVERY
from api.models.api import ApiKey
from api.models.outbox import OutboxEvent


async def of_company(session: AsyncSession, company_id: uuid.UUID) -> list[ApiKey]:
    """Oldest first."""
    query = select(ApiKey).where(ApiKey.company_id == company_id).order_by(ApiKey.created_at)

    return list(await session.scalars(query))


async def live_count(session: AsyncSession, company_id: uuid.UUID, now: datetime) -> int:
    """How many of the company's keys still work: never expiring, or not yet expired (a revoked
    key is deleted)."""
    query = select(func.count()).where(
        ApiKey.company_id == company_id, or_(ApiKey.expires_at.is_(None), ApiKey.expires_at > now)
    )

    return await session.scalar(query)


async def add(
    session: AsyncSession,
    company_id: uuid.UUID,
    name: str,
    shown: str,
    hashed: str,
    user_id: str,
    expires_at: datetime | None,
    permissions: list[str],
    allowed_ips: list[str],
    limit: int,
) -> ApiKey | None:
    """None when the company already has `limit` keys. One company's keys are added one at a
    time, so two at once can't both pass the count. The company's action log gets it as
    `user_id`'s."""
    count = select(func.count()).select_from(ApiKey).where(ApiKey.company_id == company_id)
    key = ApiKey(
        company_id=company_id,
        name=name,
        shown=shown,
        hash=hashed,
        created_by=user_id,
        expires_at=expires_at,
        permissions=permissions,
        allowed_ips=allowed_ips,
    )
    await session.execute(
        select(func.pg_advisory_xact_lock(func.hashtext(f"api_keys:{company_id}")))
    )

    if await session.scalar(count) >= limit:
        return None

    session.add(key)
    await session.flush()
    await session.refresh(key)
    audit.add(
        session,
        OutboxEvent,
        company_id,
        user_id,
        AuditAction.API_KEY_CREATED,
        TargetKind.API_KEY,
        key.id,
        name,
    )

    return key


async def by_hash(session: AsyncSession, hashed: str) -> ApiKey | None:
    return await session.scalar(select(ApiKey).where(ApiKey.hash == hashed))


async def used(session: AsyncSession, key_id: uuid.UUID) -> None:
    """Notes the key was just used, at most once a minute (LAST_USED_EVERY)."""
    now = datetime.now(UTC)
    query = (
        update(ApiKey)
        .where(
            ApiKey.id == key_id,
            or_(ApiKey.last_used_at.is_(None), ApiKey.last_used_at < now - LAST_USED_EVERY),
        )
        .values(last_used_at=now)
    )
    await session.execute(query)


async def change_permissions(
    session: AsyncSession,
    company_id: uuid.UUID,
    key_id: uuid.UUID,
    permissions: list[str],
    user_id: str,
) -> ApiKey | None:
    """Replaces the key's permissions with `permissions`; the key is locked meanwhile, so two
    changes at once apply one after the other. None when the company has no such key. The
    company's action log gets the change, when there is one, as `user_id`'s, with what was
    taken away."""
    query = (
        select(ApiKey).where(ApiKey.company_id == company_id, ApiKey.id == key_id).with_for_update()
    )
    key = await session.scalar(query)

    if key is None:
        return None

    if set(permissions) != set(key.permissions):
        removed = [item for item in key.permissions if item not in permissions]
        audit.add(
            session,
            OutboxEvent,
            company_id,
            user_id,
            AuditAction.API_KEY_PERMISSIONS_CHANGED,
            TargetKind.API_KEY,
            key_id,
            key.name,
            removed or None,
        )

    key.permissions = permissions
    await session.flush()

    return key


async def set_allowed_ips(
    session: AsyncSession,
    company_id: uuid.UUID,
    key_id: uuid.UUID,
    allowed_ips: list[str],
    user_id: str,
) -> ApiKey | None:
    """Replaces the key's allowed addresses; None when the company has no such key. The
    company's action log gets the change, when there is one, as `user_id`'s."""
    query = (
        select(ApiKey).where(ApiKey.company_id == company_id, ApiKey.id == key_id).with_for_update()
    )
    key = await session.scalar(query)

    if key is None:
        return None

    if list(key.allowed_ips) != allowed_ips:
        key.allowed_ips = allowed_ips
        audit.add(
            session,
            OutboxEvent,
            company_id,
            user_id,
            AuditAction.API_KEY_IPS_CHANGED,
            TargetKind.API_KEY,
            key_id,
            key.name,
        )
        await session.flush()

    return key


async def get(session: AsyncSession, company_id: uuid.UUID, key_id: uuid.UUID) -> ApiKey | None:
    query = select(ApiKey).where(ApiKey.company_id == company_id, ApiKey.id == key_id)

    return await session.scalar(query)


async def remove(
    session: AsyncSession, company_id: uuid.UUID, key_id: uuid.UUID, user_id: str
) -> bool:
    """Whether there was such a key of the company; the company's action log gets it as
    `user_id`'s."""
    query = (
        delete(ApiKey)
        .where(ApiKey.company_id == company_id, ApiKey.id == key_id)
        .returning(ApiKey.name)
    )
    name = await session.scalar(query)

    if name is not None:
        audit.add(
            session,
            OutboxEvent,
            company_id,
            user_id,
            AuditAction.API_KEY_DELETED,
            TargetKind.API_KEY,
            key_id,
            name,
        )

    return name is not None


async def remove_company(session: AsyncSession, company_id: uuid.UUID) -> None:
    await session.execute(delete(ApiKey).where(ApiKey.company_id == company_id))


async def of_user(session: AsyncSession, user_id: str) -> list[ApiKey]:
    return list(await session.scalars(select(ApiKey).where(ApiKey.created_by == user_id)))


async def forget_user(session: AsyncSession, user_id: str) -> None:
    """The keys the user made stay the company's, without the user's id."""
    query = update(ApiKey).where(ApiKey.created_by == user_id).values(created_by=None)
    await session.execute(query)


async def names(
    session: AsyncSession, company_id: uuid.UUID, key_ids: list[uuid.UUID]
) -> dict[uuid.UUID, str]:
    """The names the company's keys with those ids have now; deleted ones are left out."""
    query = select(ApiKey.id, ApiKey.name).where(
        ApiKey.company_id == company_id, ApiKey.id.in_(key_ids)
    )

    return {key_id: name for key_id, name in await session.execute(query)}
