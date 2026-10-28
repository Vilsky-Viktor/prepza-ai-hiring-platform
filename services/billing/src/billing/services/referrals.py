from prepza_common.config.constants import MAX_PAGE_SIZE
from prepza_common.events.analytics import track
from prepza_common.events.notifications import (
    NOTIFICATION_REQUESTED,
    NotificationKind,
    notification,
)

from billing.constants.credits import REFERRAL_REWARD
from billing.constants.notifications import REFERRAL_LINK
from billing.repositories import referrals
from billing.schemas.billing import ReferralOut, ReferralRewardOut
from billing.services import credit_events


async def referral_out(owner_type: str, owner_id: str) -> ReferralOut:
    return ReferralOut(
        code=await referrals.code_of(owner_type, owner_id),
        reward=REFERRAL_REWARD,
        rewarded=await referrals.rewarded_count(owner_type, owner_id),
        rewards=[
            ReferralRewardOut(company_id=row.owner_id, rewarded_at=row.rewarded_at, credits=paid)
            for row, paid in await referrals.rewards(owner_type, owner_id, MAX_PAGE_SIZE)
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

    referrer_id = await referrals.reward(owner_type, owner_id, transaction_id, told)

    if referrer_id is not None:
        await track("referral_rewarded", company_id=owner_id)


async def take_back_reward(owner_id: str, transaction_id: str) -> None:
    """A top-up refunded in full or charged back no longer pays its referral."""
    if await referrals.take_back(transaction_id):
        await track("referral_reversed", company_id=owner_id)
