import uuid

from companies.repositories import companies, members, superadmin_companies


def test_companies_are_found_by_name_with_their_people_and_suspended_and_lifted(run):
    tag = uuid.uuid4().hex[:8]

    async def scenario():
        found = await companies.create(f"Impostor {tag}", f"ann-{tag}", "ann@example.com")
        other = await companies.create(f"Other {tag}", f"cid-{tag}", "cid@example.com")
        bob = await members.add(found.id, "bob@example.com", "admin", {})
        await members.accept(bob, found, f"bob-{tag}")
        listed = await superadmin_companies.search(f"IMPOSTOR {tag}", 10)
        suspended = await superadmin_companies.set_suspended(found.id, True)
        while_suspended = await companies.get(found.id)
        await superadmin_companies.set_suspended(found.id, False)
        lifted = await companies.get(found.id)
        missing = await superadmin_companies.set_suspended(uuid.uuid4(), True)

        for company in (found, other):
            await companies.delete(company.id)

        return listed, suspended, while_suspended, lifted, missing, found.id

    listed, suspended, while_suspended, lifted, missing, found_id = run(scenario())

    # Whatever the case; the owner and Bob joined.
    assert [(company.id, people) for company, people in listed] == [(found_id, 2)]
    assert suspended and while_suspended.suspended_at is not None
    assert lifted.suspended_at is None
    assert missing is False
