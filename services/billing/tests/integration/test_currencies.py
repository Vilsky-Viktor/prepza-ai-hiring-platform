import asyncio
import uuid

from app.constants.currencies import ChoiceOwner
from app.services.currencies import decide
from app.storage import currencies


def test_a_currency_is_saved_once_from_a_country_and_kept_until_changed(run):
    acme, ann = str(uuid.uuid4()), f"user-{uuid.uuid4()}"

    async def scenario():
        # No country yet: dollars, nothing saved.
        unknown = await decide(None, company_id=acme)
        none_saved = await currencies.chosen(ChoiceOwner.COMPANY, acme)
        # Two first requests at once from Germany: one is saved.
        first = await asyncio.gather(decide("DE", company_id=acme), decide("de", company_id=acme))
        # Seen later from the UK, or from nowhere: still euros.
        travelled = await decide("GB", company_id=acme)
        no_country = await decide(None, company_id=acme)
        # Changed to pounds; the person's own is apart from the company's.
        await currencies.choose(ChoiceOwner.COMPANY, acme, "GBP")
        changed = await decide("DE", company_id=acme)
        person = await decide("US", user_id=ann)
        # Deleted with the company.
        await currencies.forget(ChoiceOwner.COMPANY, acme)

        return (
            unknown,
            none_saved,
            first,
            travelled,
            no_country,
            changed,
            person,
            await currencies.chosen(ChoiceOwner.COMPANY, acme),
            await currencies.chosen(ChoiceOwner.USER, ann),
        )

    unknown, none_saved, first, travelled, no_country, changed, person, gone, kept = run(scenario())

    assert (unknown, none_saved) == ("USD", None)
    assert first == ["EUR", "EUR"]
    assert (travelled, no_country, changed) == ("EUR", "EUR", "GBP")
    assert (person, kept) == ("USD", "USD")
    assert gone is None
