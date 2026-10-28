import uuid

from companies.repositories import interviews, invites
from tests.integration.repositories.test_invites import interview


def test_the_companies_that_invited_an_address_are_found_once_whatever_its_case(run):
    address = f"gil-{uuid.uuid4()}@example.com"

    async def scenario():
        first, second, other = await interview(), await interview(), await interview()
        again = await interviews.create(first.company_id, uuid.uuid4(), "en", 60)

        for found in (first, again, second):
            await invites.upsert(found.id, address.upper(), "Backend", "Acme", "en")

        await invites.upsert(other.id, "someone-else@example.com", "Backend", "Acme", "en")

        return await invites.company_ids_for(f" {address.title()} "), {
            str(first.company_id),
            str(second.company_id),
        }

    found, expected = run(scenario())

    assert sorted(found) == sorted(expected)
