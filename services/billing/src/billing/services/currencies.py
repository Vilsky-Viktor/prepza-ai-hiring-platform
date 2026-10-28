from billing.constants.currencies import DEFAULT_CURRENCY, ChoiceOwner, Currency
from billing.helpers.currencies import currency_for, known_country
from billing.repositories import currencies


async def saved(owner_type: ChoiceOwner, owner_id: str, country: str | None) -> Currency:
    """The owner's saved currency. One without yet gets their country's, saved the first time
    billing sees them with a known country (US dollars until then), so travelling later changes
    nothing."""
    found = await currencies.chosen(owner_type, owner_id)

    if found:
        return Currency(found)

    if not known_country(country):
        return DEFAULT_CURRENCY

    return Currency(await currencies.remember(owner_type, owner_id, currency_for(country)))


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
