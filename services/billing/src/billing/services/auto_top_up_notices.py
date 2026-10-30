from datetime import datetime

from prepza_common.events.notifications import NotificationKind, notification

from billing.constants.notifications import COMPANY_BILLING_LINK
from billing.models.billing import AutoTopUp
from billing.services.auto_top_up_prices import charge_price


def turned_on(row: AutoTopUp, subscription_id: str, now: datetime) -> dict:
    """The notice that automatic top-up is on, its card saved: what each charge costs (plus tax)
    and the level that starts one, for the bell and an email to the company's owners and admins.
    It opens the company's billing page, where it's turned off. One per subscription."""
    return notification(
        row.owner_type,
        row.owner_id,
        NotificationKind.AUTO_TOP_UP_ON,
        COMPANY_BILLING_LINK.format(owner_id=row.owner_id),
        key=subscription_id,
        price=charge_price(row, row.currency, now),
        currency=row.currency,
        threshold=row.threshold,
    )


def charged(
    owner_type: str,
    owner_id: str,
    transaction_id: str,
    credits: int,
    total: str,
    currency: str,
    day: str,
) -> dict:
    """The notice of one automatic charge: the credits it added, what the card paid (tax
    included), the day, and (filled in by the grant) the credits available after it. It opens
    the company's billing page, where automatic top-up is turned off. One per transaction."""
    return notification(
        owner_type,
        owner_id,
        NotificationKind.AUTO_TOP_UP_CHARGED,
        COMPANY_BILLING_LINK.format(owner_id=owner_id),
        key=transaction_id,
        credits=credits,
        price=int(total),
        currency=currency,
        date=day,
    )
