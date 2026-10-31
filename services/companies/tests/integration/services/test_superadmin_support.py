"""The admin zone's support tab against the real database: one company with a member, an
interview and a candidate, made and removed by each test. Library is faked: no accounts."""

import uuid

import pytest

from companies.integrations import accounts
from companies.repositories import interviews, invites, superadmin_support
from companies.services import support_search
from tests.integration import factories
from tests.integration.transactions import transaction


@pytest.fixture(autouse=True)
def no_accounts(monkeypatch):
    async def none(text):
        return None

    monkeypatch.setattr(accounts, "account", none)
    monkeypatch.setattr(accounts, "account_by_email", none)


def test_a_support_search_finds_a_company_its_interview_and_its_candidate(run):
    tag = uuid.uuid4().hex[:8]
    member = f"bob-{tag}@example.com"
    candidate = f"cid-{tag}@example.com"

    async def scenario():
        acme = await factories.company(f"Support {tag}", f"ann-{tag}", f"ann-{tag}@example.com")
        await factories.member(acme.id, member, "admin", {})
        interview = await transaction(interviews.create, acme.id, uuid.uuid4(), "en", 60)
        await transaction(interviews.set_title, interview.id, "Backend")
        invite, _ = await transaction(
            invites.upsert, interview.id, candidate, "Backend", acme.name, "en"
        )
        link = f"https://testee.com/de/companies/{acme.id}/interviews/{interview.id}"

        def found(rows):
            return [(row.kind, row.id, row.title, row.company_id) for row in rows]

        searches = [
            await support_search.search(query)
            for query in (
                str(acme.id),
                str(interview.id),
                str(invite.id),
                link,
                f"{link}/candidates/{invite.id}",
                member.upper(),
                candidate.upper(),
                f"SUPPORT {tag}",
                # The owner's account id, as "copy id" in their menu gives it.
                f"ann-{tag}",
                str(uuid.uuid4()),
                f"nobody-{tag}@example.com",
            )
        ]
        await factories.deleted(acme.id)

        return [found(rows) for rows in searches], acme, interview, invite

    results, acme, interview, invite = run(scenario())
    company = ("company", str(acme.id), acme.name, acme.id)
    test = ("interview", str(interview.id), "Backend", acme.id)
    person = ("candidate", str(invite.id), candidate, acme.id)

    assert results == [
        [company],
        [test],
        [person],
        [test],
        [person],
        # Whatever the case: the member's company, the candidate with theirs.
        [company],
        [person],
        [company],
        [company],
        [],
        [],
    ]


def test_a_candidate_and_an_interview_come_with_their_company_and_an_account_with_its_roles(run):
    tag = uuid.uuid4().hex[:8]

    async def scenario():
        acme = await factories.company(f"Support {tag}", f"ann-{tag}", f"ann-{tag}@example.com")
        interview = await transaction(interviews.create, acme.id, uuid.uuid4(), "en", 60)
        invite, _ = await transaction(
            invites.upsert, interview.id, f"cid-{tag}@example.com", "", acme.name, "en"
        )
        found = (
            await transaction(superadmin_support.candidate, invite.id),
            await transaction(superadmin_support.interview, interview.id),
            await transaction(superadmin_support.companies_of_user, f"ann-{tag}", 10),
            await transaction(superadmin_support.candidate, uuid.uuid4()),
            await transaction(superadmin_support.interview, uuid.uuid4()),
            await transaction(superadmin_support.companies_of_user, f"nobody-{tag}", 10),
        )
        await factories.deleted(acme.id)

        return found, acme, interview, invite

    found, acme, interview, invite = run(scenario())
    candidate, test, roles, *missing = found

    assert [row.id for row in candidate] == [invite.id, interview.id, acme.id]
    assert [row.id for row in test] == [interview.id, acme.id]
    assert [(company.id, role) for company, role in roles] == [(acme.id, "owner")]
    assert missing == [None, None, []]
