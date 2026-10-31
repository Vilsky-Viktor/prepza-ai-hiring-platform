import secrets
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from testee_common.config.constants import DELETED_USER

from billing.constants.credits import (
    REFERRAL_CODE_BYTES,
    REFERRAL_REWARD,
    REFERRALS_PER_YEAR,
    Reason,
)
from billing.models.billing import Entry, Referral, Wallet
from billing.repositories.events import save
from billing.repositories.ledger import add, ensure


async def code_of(session: AsyncSession, owner_type: str, owner_id: str) -> str:
    """The owner's referral code, made the first time it's asked for."""
    await ensure(session, owner_type, owner_id)
    row = await session.get(
        Wallet, (owner_type, owner_id), with_for_update=True, populate_existing=True
    )

    if row.referral_code is None:
        row.referral_code = secrets.token_urlsafe(REFERRAL_CODE_BYTES)

    return row.referral_code


async def record(
    session: AsyncSession, code: str, owner_type: str, owner_id: str, related: list[str]
) -> bool:
    """Notes that a new company came through another company's link: the wallet with that code,
    other than the new company and those related to it. The first link counts."""
    referrer_id = await session.scalar(
        select(Wallet.owner_id).where(
            Wallet.referral_code == code,
            Wallet.owner_type == owner_type,
            Wallet.owner_id != owner_id,
            Wallet.owner_id.not_in(related),
        )
    )

    if referrer_id is None:
        return False

    new = await session.scalar(
        insert(Referral)
        .values(owner_type=owner_type, owner_id=owner_id, referrer_id=referrer_id)
        .on_conflict_do_nothing()
        .returning(Referral.owner_id)
    )

    return new is not None


def reward_key(owner_type: str, owner_id: str, transaction_id: str) -> str:
    return f"referral:{owner_type}:{owner_id}:{transaction_id}"


async def reward(
    session: AsyncSession,
    owner_type: str,
    owner_id: str,
    transaction_id: str,
    events_for: Callable[[str], list[tuple[str, dict]]] = lambda referrer_id: [],
) -> str | None:
    """Pays a referral once its new company has topped up (`transaction_id`): both sides get
    the reward, the referrer only within their yearly limit and while their wallet exists, with
    `events_for(referrer)` for the outbox in the same transaction. The referrer's id when it was
    paid."""
    amount = REFERRAL_REWARD
    now = datetime.now(UTC)
    key = reward_key(owner_type, owner_id, transaction_id)

    # A top-up pays at most once: a redelivery after its reward was taken back (refund)
    # leaves the referral for the next real top-up.
    if await session.scalar(select(Entry.key).where(Entry.key == key)):
        return None

    referrer_id = await session.scalar(
        update(Referral)
        .where(
            Referral.owner_type == owner_type,
            Referral.owner_id == owner_id,
            Referral.rewarded_at.is_(None),
        )
        .values(rewarded_at=now, rewarded_by=transaction_id)
        .returning(Referral.referrer_id)
    )

    if referrer_id is None:
        return None

    await add(session, owner_type, owner_id, amount, key, Reason.REFERRAL)
    # The referrer's wallet is locked before counting, so rewards from two of their
    # companies at once count each other and can't both pass the limit.
    referrer = await session.get(Wallet, (owner_type, referrer_id), with_for_update=True)
    rewarded_this_year = await session.scalar(
        select(func.count()).where(
            Referral.owner_type == owner_type,
            Referral.referrer_id == referrer_id,
            Referral.rewarded_at > now - timedelta(days=365),
        )
    )
    # This one is already counted, hence <=.
    paid = referrer is not None and rewarded_this_year <= REFERRALS_PER_YEAR

    if paid:
        referrer_key = f"{key}:referrer"

        # Told only when the reward moved, never again for one paid before.
        if await add(session, owner_type, referrer_id, amount, referrer_key, Reason.REFERRAL):
            save(session, events_for(referrer_id))

    # Over their yearly limit, or deleted: nothing to tell them.
    return referrer_id if paid else None


async def take_back(session: AsyncSession, transaction_id: str) -> bool:
    """The top-up that paid a referral was refunded in full or charged back: both sides' rewards
    go back (from wallets that still exist), and the referral waits for the company's next
    top-up. Once per transaction, however often Paddle sends the adjustment. True when there
    was a reward to take back."""
    referral = await session.scalar(
        update(Referral)
        .where(Referral.rewarded_by == transaction_id)
        .values(rewarded_at=None, rewarded_by=None)
        .returning(Referral)
    )

    if referral is None:
        return False

    key = reward_key(referral.owner_type, referral.owner_id, transaction_id)
    paid = await session.scalars(select(Entry).where(Entry.key.in_([key, f"{key}:referrer"])))

    for entry in list(paid):
        await add(
            session,
            entry.owner_type,
            entry.owner_id,
            -entry.amount,
            f"{entry.key}:reversed",
            Reason.REFERRAL_REVERSED,
        )

    return True


async def rewarded_count(session: AsyncSession, owner_type: str, owner_id: str) -> int:
    """How many companies the owner brought in that have been rewarded."""
    return await session.scalar(
        select(func.count()).where(
            Referral.owner_type == owner_type,
            Referral.referrer_id == owner_id,
            Referral.rewarded_at.is_not(None),
        )
    )


async def rewards(
    session: AsyncSession, owner_type: str, owner_id: str, limit: int
) -> list[tuple[Referral, int]]:
    """The companies the owner brought in that have been rewarded, newest first, each with the
    credits it paid the owner: what was given then, and 0 when the owner was over the yearly
    limit."""
    query = (
        select(Referral)
        .where(
            Referral.owner_type == owner_type,
            Referral.referrer_id == owner_id,
            Referral.rewarded_at.is_not(None),
        )
        .order_by(Referral.rewarded_at.desc())
        .limit(limit)
    )
    rows = list(await session.scalars(query))
    keys = {
        row.owner_id: f"{reward_key(row.owner_type, row.owner_id, row.rewarded_by)}:referrer"
        for row in rows
    }
    paid = dict(
        (
            await session.execute(
                select(Entry.key, Entry.amount).where(
                    Entry.owner_type == owner_type,
                    Entry.owner_id == owner_id,
                    Entry.key.in_(keys.values()),
                )
            )
        ).all()
    )

    return [(row, paid.get(keys[row.owner_id], 0)) for row in rows]


async def forget(session: AsyncSession, owner_type: str, owner_id: str) -> None:
    """On deletion: the owner's own referral goes, unless it was rewarded: kept (only ids and
    the top-up that paid it), a refund of that top-up still takes the referrer's reward back,
    so deleting a referred company can't keep it. The ones they made lose their name, so the
    people they brought in still get their own reward."""
    is_owner = {"owner_type": owner_type}
    await session.execute(
        delete(Referral)
        .filter_by(**is_owner, owner_id=owner_id)
        .where(Referral.rewarded_by.is_(None))
    )
    await session.execute(
        update(Referral)
        .filter_by(**is_owner, referrer_id=owner_id)
        .values(referrer_id=DELETED_USER)
    )
