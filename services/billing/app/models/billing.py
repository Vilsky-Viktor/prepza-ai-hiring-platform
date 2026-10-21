import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.currencies import CURRENCY_CHECK, PRICE_CURRENCY_CHECK
from app.models.base import Base


class Wallet(Base):
    """One credit balance. `reserved` is set aside for something that hasn't finished."""

    __tablename__ = "wallets"

    owner_type: Mapped[str] = mapped_column(String(16), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    balance: Mapped[int] = mapped_column(default=0)
    reserved: Mapped[int] = mapped_column(default=0)
    # The code in the owner's referral link; made the first time they ask for it.
    referral_code: Mapped[str | None] = mapped_column(String(16), unique=True)


class Referral(Base):
    """A new company that came through another company's link. `rewarded_at` is set when
    their first top-up pays both sides, and `rewarded_by` is that top-up's transaction; a full
    refund of it takes the rewards back and clears both."""

    __tablename__ = "referrals"

    owner_type: Mapped[str] = mapped_column(String(16), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    referrer_id: Mapped[str] = mapped_column(String(128), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )
    rewarded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rewarded_by: Mapped[str | None] = mapped_column(String(64), index=True)


class AutoTopUp(Base):
    """A wallet's automatic top-up: the top-up to buy when the available balance falls under
    `threshold`. Waiting for its checkout until `subscription_id` is set; `charged_at` is the
    last automatic charge, `failed_at` the last one the card declined."""

    __tablename__ = "auto_top_ups"
    __table_args__ = (
        CheckConstraint(CURRENCY_CHECK, name="ck_auto_top_ups_currency"),
        CheckConstraint(PRICE_CURRENCY_CHECK, name="ck_auto_top_ups_price_currency"),
    )

    owner_type: Mapped[str] = mapped_column(String(16), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    product: Mapped[str] = mapped_column(String(64))
    threshold: Mapped[int]
    # Who turned it on; only their checkout can start it.
    buyer_id: Mapped[str] = mapped_column(String(128))
    subscription_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    # The currency Paddle bills the subscription in: set when it starts, and switched to the
    # company's before a charge when that changed.
    currency: Mapped[str | None] = mapped_column(String(3))
    charged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Declines in a row since the last charge that went through; the next try waits until
    # `retry_at`. Paused (`paused_at`) after a decline that can't pass later, or too many: no
    # charge until the card is updated.
    declines: Mapped[int] = mapped_column(default=0, server_default="0")
    retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # What each charge costs (minor units, in `price_currency`), as agreed: the price when it was
    # set up, until a new price is announced (`next_price`) and its day (`next_price_from`)
    # comes. None until the first charge or the first daily check.
    price: Mapped[int | None] = mapped_column(BigInteger)
    price_currency: Mapped[str | None] = mapped_column(String(3))
    next_price: Mapped[int | None] = mapped_column(BigInteger)
    next_price_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CurrencyChoice(Base):
    """The currency a company pays in, or a person sees prices in, whoever and wherever they
    are; without a row, the visitor's country decides (helpers/currencies.py)."""

    __tablename__ = "currency_choices"
    __table_args__ = (CheckConstraint(CURRENCY_CHECK, name="ck_currency_choices_currency"),)

    owner_type: Mapped[str] = mapped_column(String(16), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    currency: Mapped[str] = mapped_column(String(3))


class Gift(Base):
    """A welcome gift already given, by a one-way hash of the email. Kept when the account or
    company is deleted, so signing up again doesn't give the gift again."""

    __tablename__ = "gifts"

    key: Mapped[str] = mapped_column(String(160), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )


class Hold(Base):
    """Credits set aside for one piece of work, charged or given back later."""

    __tablename__ = "holds"

    key: Mapped[str] = mapped_column(String(160), primary_key=True)
    owner_type: Mapped[str] = mapped_column(String(16))
    owner_id: Mapped[str] = mapped_column(String(128))
    amount: Mapped[int]
    reason: Mapped[str] = mapped_column(String(64))
    # open, charged or released.
    status: Mapped[str] = mapped_column(String(16))


class Entry(Base):
    """One movement of credits: a gift or top-up (positive), or a charge (negative). The key
    makes a repeated call count once. Together they're the wallet's history. A top-up, refund or
    chargeback also keeps the money it moved, and a top-up whether it was automatic."""

    __tablename__ = "entries"
    __table_args__ = (
        UniqueConstraint("key", name="uq_entries_key"),
        # A wallet's history, newest first, a page at a time (storage/history.py).
        Index("ix_entries_history", "owner_type", "owner_id", text("created_at DESC"), "id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(160))
    owner_type: Mapped[str] = mapped_column(String(16))
    owner_id: Mapped[str] = mapped_column(String(128), index=True)
    amount: Mapped[int]
    reason: Mapped[str] = mapped_column(String(64))
    # In the currency's minor units, tax included, as Paddle gives it; None for a movement that
    # moved no money (a gift, a charge) or one from before it was kept.
    total_minor: Mapped[int | None] = mapped_column(BigInteger)
    currency: Mapped[str | None] = mapped_column(String(3))
    automatic: Mapped[bool] = mapped_column(default=False, server_default="false")
    # A superadmin's adjustment: why, as the company's history shows it.
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )


class Purchase(Base):
    """One paid Paddle transaction line. Kept for bookkeeping; anonymised when the buyer deletes
    their account."""

    __tablename__ = "purchases"
    __table_args__ = (
        UniqueConstraint("transaction_id", "product", name="uq_purchases_transaction_product"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    transaction_id: Mapped[str] = mapped_column(String(64), index=True)
    product: Mapped[str] = mapped_column(String(64))
    quantity: Mapped[int]
    owner_type: Mapped[str] = mapped_column(String(16))
    owner_id: Mapped[str] = mapped_column(String(128), index=True)
    # Who paid, when a company buys; the company is the owner.
    buyer_id: Mapped[str | None] = mapped_column(String(128))
    # What the whole transaction cost, in minor units, tax included.
    total_minor: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )
