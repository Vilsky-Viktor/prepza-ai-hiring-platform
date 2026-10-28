from prepza_common.config.constants import MAX_PAGE_SIZE
from prepza_common.events.analytics import track
from prepza_common.events.notifications import (
    NOTIFICATION_REQUESTED,
    NotificationKind,
    notification,
)

from billing.constants.credits import REFERRAL_REWARD
from billing.constants.notifications import REFERRAL_LINK
from billing.core.db import Session
from billing.repositories import referrals
from billing.schemas.billing import ReferralOut, ReferralRewardOut
from billing.services import credit_events


async def referral_out(owner_type: str, owner_id: str) -> ReferralOut:
    """The owner's referral code (made the first time it's asked for) and the rewards it paid."""
    async with Session.begin() as session:
        code = await referrals.code_of(session, owner_type, owner_id)
        rewarded = await referrals.rewarded_count(session, owner_type, owner_id)
        rewards = await referrals.rewards(session, owner_type, owner_id, MAX_PAGE_SIZE)

    return ReferralOut(
        code=code,
        reward=REFERRAL_REWARD,
        rewarded=rewarded,
        rewards=[
            ReferralRewardOut(company_id=row.owner_id, rewarded_at=row.rewarded_at, credits=paid)
            for row, paid in rewards
        ],
    )


async def reward_after_top_up(owner_type: str, owner_id: str, transaction_id: str) -> None:
    """The first top-up pays the referral its company came through, once, and tells the
    referrer."""

    def told(referrer_id: str) -> list[tuple[str, dict]]:
        # The referrer got the reward too (the company that topped up hears of its top-up).
        notice = notification(
            owner_type,
            referrer_id,
            NotificationKind.REFERRAL_REWARDED,
            REFERRAL_LINK.format(owner_id=referrer_id),
            credits=REFERRAL_REWARD,
        )

        return [
            credit_events.credits_added(owner_type, referrer_id),
            (NOTIFICATION_REQUESTED, notice),
        ]

    async with Session.begin() as session:
        referrer_id = await referrals.reward(session, owner_type, owner_id, transaction_id, told)

    if referrer_id is not None:
        await track("referral_rewarded", company_id=owner_id)


async def take_back_reward(owner_id: str, transaction_id: str) -> None:
    """A top-up refunded in full or charged back no longer pays its referral."""
    async with Session.begin() as session:
        taken = await referrals.take_back(session, transaction_id)

    if taken:
        await track("referral_reversed", company_id=owner_id)
