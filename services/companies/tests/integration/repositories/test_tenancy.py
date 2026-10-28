"""Invites carry their company, and a person is a member of a company once."""

import uuid

from sqlalchemy.exc import IntegrityError

from companies.core.db import Session
from companies.models.companies import Member
from companies.repositories import interviews, invites, link_invites
from tests.integration import factories
from tests.integration.transactions import transaction


def test_an_invite_carries_its_interviews_company_however_it_was_made(run):
    async def scenario():
        company = await factories.company(f"Tenancy {uuid.uuid4()}", "owner", "o@example.com")
        interview = await transaction(interviews.create, company.id, uuid.uuid4(), "en", 60)
        sent, _ = await transaction(
            invites.upsert, interview.id, "ann@example.com", "Backend", "Acme", "en"
        )
        joined = await transaction(link_invites.for_link, interview.id, "bob@example.com")

        return company.id, sent.company_id, joined.company_id

    company, sent, joined = run(scenario())

    assert sent == joined == company


def test_the_database_refuses_a_second_membership_of_one_person(run):
    async def scenario():
        company = await factories.company(f"Twice {uuid.uuid4()}", "ann", "ann@example.com")

        async with Session() as session:
            session.add(
                Member(
                    company_id=company.id,
                    user_id="ann",
                    invited_email="other@example.com",
                    role="viewer",
                )
            )

            try:
                await session.commit()
            except IntegrityError as error:
                return error.orig.diag.constraint_name

    assert run(scenario()) == "uq_members_company_user"
