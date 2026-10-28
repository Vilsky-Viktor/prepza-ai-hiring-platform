"""Each action whose steps must succeed together is one save: when a later step fails, nothing
the earlier steps wrote is kept, so the caller's retry finds the whole action still to do."""

import uuid
from datetime import UTC, datetime

import pytest

from billing.constants.currencies import ChoiceOwner, Currency
from billing.constants.products import TOP_UPS, OwnerType
from billing.repositories import auto_top_ups, currencies, ledger, purchases, referrals
from billing.schemas.billing import AutoTopUpIn, WelcomeIn
from billing.services import accounts, topups, wallets
from billing.services import auto_top_ups as auto_top_up_service
from tests.integration.factories import welcomed
from tests.integration.transactions import transaction

COMPANY = OwnerType.COMPANY
NOW = datetime(2026, 10, 28, 12, tzinfo=UTC)


async def broken(*args):
    raise RuntimeError("The database went away")


@pytest.mark.parametrize(
    ("module", "step"),
    [(referrals, "record"), (currencies, "remember")],
    ids=["referral", "currency"],
)
def test_a_welcome_whose_later_step_fails_gives_no_credits_yet(run, monkeypatch, module, step):
    """The welcome credits, the referral and the currency are one save: a failed referral or
    currency leaves no wallet, so the company's retry gets the credits then."""
    acme = str(uuid.uuid4())
    body = WelcomeIn(owner_email=f"{acme}@example.com", country="IE", referral="ref-code")
    monkeypatch.setattr(module, step, broken)

    async def scenario():
        with pytest.raises(RuntimeError):
            await wallets.welcome(acme, body)

        return (
            await transaction(ledger.wallets, COMPANY, [acme]),
            await transaction(ledger.has_entry, f"welcome:{acme}"),
        )

    assert run(scenario()) == ({}, False)


def test_a_company_deletion_whose_currency_fails_keeps_its_wallet(run, monkeypatch):
    """The wallet, the referral and the currency go together: a failure leaves the wallet for
    the deletion's retry."""
    acme = str(uuid.uuid4())

    async def scenario():
        await welcomed(acme, f"{acme}@example.com")
        await transaction(currencies.choose, ChoiceOwner.COMPANY, acme, Currency.EUR)
        monkeypatch.setattr(currencies, "forget", broken)

        with pytest.raises(RuntimeError):
            await accounts.delete_company(acme)

        found = await transaction(ledger.wallets, COMPANY, [acme])

        return list(found), await transaction(currencies.chosen, ChoiceOwner.COMPANY, acme)

    assert run(scenario()) == ([acme], Currency.EUR)


def test_a_user_deletion_whose_currency_fails_keeps_what_they_bought_and_turned_on(
    run, monkeypatch, paddle_calls
):
    """Their automatic top-ups going off, their purchases losing their id and their currency go
    together: a failure leaves all of it for the deletion's retry."""
    acme, ann = str(uuid.uuid4()), f"user-{uuid.uuid4()}"
    choice = AutoTopUpIn(product="topup_50", threshold=500)

    async def scenario():
        await welcomed(acme, f"{acme}@example.com")
        await topups.grant(
            COMPANY, acme, 1_000, 1, f"txn_{acme}", TOP_UPS[0].key, ann, "1000", "USD", NOW
        )
        await auto_top_up_service.turn_on(COMPANY, acme, choice, ann, Currency.USD)
        await transaction(currencies.choose, ChoiceOwner.USER, ann, Currency.EUR)
        monkeypatch.setattr(currencies, "forget", broken)

        with pytest.raises(RuntimeError):
            await accounts.delete_user(ann)

        bought = await transaction(purchases.purchases_of, ann)
        turned_on = await transaction(auto_top_ups.of_buyer, ann)

        return len(bought), [row.owner_id for row in turned_on]

    assert run(scenario()) == (1, [acme])
