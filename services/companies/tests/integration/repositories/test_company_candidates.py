import uuid

from companies.repositories import candidates, companies, interviews, invites


async def company_with_interview(title: str):
    company = await companies.create(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")

    return company, await interview_of(company, title)


async def interview_of(company, title: str):
    found = await interviews.create(company.id, uuid.uuid4(), "en", 60)
    await interviews.set_title(found.id, title)

    return found


async def invite(found, email):
    await invites.upsert(found.id, email, found.title or "", "Acme", "en")


def rows(listed):
    return [(invite.email, interview.title) for invite, interview in listed]


def test_a_companys_candidates_are_found_across_its_interviews_newest_first(run):
    async def scenario():
        company, backend = await company_with_interview("Backend")
        frontend = await interview_of(company, "Frontend")
        gone = await interview_of(company, "Gone")
        _, elsewhere = await company_with_interview("Elsewhere")
        # Invited in this order, so newest first is cleo, ben, ann.
        await invite(backend, "ann@example.com")
        await invite(frontend, "ben@example.com")
        await invite(frontend, "cleo@example.com")
        await invite(gone, "dan@example.com")
        await invite(elsewhere, "ann@example.com")
        # A deleted interview's candidates go with it.
        await interviews.remove(gone.id)

        def listed(offset, limit, q=""):
            return candidates.company_page(company.id, offset, limit, q)

        return (
            rows(await listed(0, 2)) + rows(await listed(2, 2)),
            rows(await listed(0, 10, "ANN@")),
            rows(await listed(0, 10, "c_")),
        )

    paged, by_email, underscore = run(scenario())

    assert paged == [
        ("cleo@example.com", "Frontend"),
        ("ben@example.com", "Frontend"),
        ("ann@example.com", "Backend"),
    ]
    # Only this company's ann, matched in any case.
    assert by_email == [("ann@example.com", "Backend")]
    # An underscore is matched as typed, not as any character.
    assert underscore == []


def test_a_companys_candidates_are_found_by_exactly_their_email(run):
    async def scenario():
        company, backend = await company_with_interview("Backend")
        frontend = await interview_of(company, "Frontend")
        await invite(backend, "ann@example.com")
        await invite(frontend, "ann@example.com")
        await invite(frontend, "joann@example.com")

        return rows(await candidates.company_page(company.id, 0, 10, email="Ann@Example.com"))

    assert run(scenario()) == [("ann@example.com", "Frontend"), ("ann@example.com", "Backend")]
