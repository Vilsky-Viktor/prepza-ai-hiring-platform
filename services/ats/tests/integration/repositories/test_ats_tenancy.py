"""ATS rows carry their connection's company, and an invite belongs to one ATS row."""

import uuid

from sqlalchemy import select

from ats.constants.ats import AtsProvider, CandidateStatus
from ats.core.db import Session
from ats.models.ats import AtsCandidate, AtsJobLink
from ats.repositories import ats, ats_candidates, ats_links
from ats.services import ats_candidates as candidate_service
from tests.integration.transactions import transaction

JOB = {"id": "A1", "name": "Accountant"}
STAGE = {"id": "assessment", "name": "Assessment"}


async def connected(company, provider):
    await transaction(ats.connect, company, provider, "acme", "sealed", "ann", "m-1")

    return await transaction(ats.connection, company, provider)


def test_links_and_candidates_carry_their_company(run):
    company, interview = uuid.uuid4(), uuid.uuid4()

    async def scenario():
        connection = await connected(company, AtsProvider.WORKABLE)
        link_id = await transaction(
            ats_links.add_link, company, connection.id, interview, JOB, STAGE, "ann"
        )
        row = await transaction(
            ats_candidates.add, connection.id, link_id, interview, "c-1", "a@x.com"
        )

        async with Session() as session:
            link = await session.get(AtsJobLink, link_id)

        return link.company_id, row.id

    link_company, row_id = run(scenario())

    async def stored():
        async with Session() as session:
            return await session.scalar(
                select(AtsCandidate.company_id).where(AtsCandidate.id == row_id)
            )

    assert (link_company, run(stored())) == (company, company)


def test_a_person_two_atss_sent_keeps_the_invite_on_the_first_row(run):
    company, interview, invite = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()

    async def scenario():
        rows = []

        for provider in (AtsProvider.WORKABLE, AtsProvider.GREENHOUSE):
            connection = await connected(company, provider)
            link_id = await transaction(
                ats_links.add_link, company, connection.id, interview, JOB, STAGE, "ann"
            )
            rows.append(
                await transaction(
                    ats_candidates.add, connection.id, link_id, interview, "c-1", "a@x.com"
                )
            )

        for row in rows:
            # The service settles a second row with the same invite without it.
            await candidate_service.settle(row.id, CandidateStatus.INVITED, invite_id=invite)

        async with Session() as session:
            return [
                await session.scalar(
                    select(AtsCandidate.invite_id).where(AtsCandidate.id == row.id)
                )
                for row in rows
            ]

    assert run(scenario()) == [invite, None]
