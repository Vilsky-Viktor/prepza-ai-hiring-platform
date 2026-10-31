from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from testee_common.events.audit_actions import AuditAction

from billing.constants.currencies import DEFAULT_CURRENCY, ChoiceOwner, Currency
from billing.constants.products import OwnerType
from billing.core.db import Session
from billing.helpers.currencies import currency_for, known_country
from billing.repositories import auto_top_ups, company_actions, currencies
from billing.schemas.billing import CompanyCurrencyOut
from billing.services.auto_top_up_prices import charge_price


async def saved_in(
    session: AsyncSession, owner_type: ChoiceOwner, owner_id: str, country: str | None
) -> Currency:
    """The owner's saved currency. One without yet gets their country's, saved the first time
    billing sees them with a known country (US dollars until then), so travelling later changes
    nothing."""
    found = await currencies.chosen(session, owner_type, owner_id)

    if found:
        return Currency(found)

    if not known_country(country):
        return DEFAULT_CURRENCY

    return Currency(await currencies.remember(session, owner_type, owner_id, currency_for(country)))


async def saved(owner_type: ChoiceOwner, owner_id: str, country: str | None) -> Currency:
    async with Session.begin() as session:
        return await saved_in(session, owner_type, owner_id, country)


async def decide(
    country: str | None, user_id: str | None = None, company_id: str | None = None
) -> Currency:
    """The currency prices are shown and charged in: the company's when it's the company's
    money, else the signed-in person's, else (signed out) their country's, not saved."""
    if company_id:
        return await saved(ChoiceOwner.COMPANY, company_id, country)

    if user_id:
        return await saved(ChoiceOwner.USER, user_id, country)

    return currency_for(country)


async def choose(owner_type: ChoiceOwner, owner_id: str, currency: Currency) -> None:
    async with Session.begin() as session:
        await currencies.choose(session, owner_type, owner_id, currency)


async def choose_company(
    company_id: str, currency: Currency, actor: str | None = None
) -> CompanyCurrencyOut:
    """From now on its top-ups are priced and charged in it, automatic ones too, at once and at
    the price list's price in it (their next charge switches the subscription over), which the
    answer says for a running one. The `actor`'s choice goes to the action log in the same
    save."""
    async with Session.begin() as session:
        await currencies.choose(session, ChoiceOwner.COMPANY, company_id, currency)
        row = await auto_top_ups.get(session, OwnerType.COMPANY, company_id)

        if actor is not None:
            company_actions.log(session, company_id, actor, AuditAction.CURRENCY_CHANGED)

    chosen = CompanyCurrencyOut(currency=currency)

    if row is not None and row.subscription_id is not None:
        chosen.auto_top_up_price = charge_price(row, currency, datetime.now(UTC))

    return chosen
