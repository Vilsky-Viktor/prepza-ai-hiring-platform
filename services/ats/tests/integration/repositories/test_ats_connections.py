"""Connections and linked jobs: connect, reconnect, credentials, links and unlinking."""

import uuid

from ats.constants.ats import AtsProvider
from ats.helpers.notifications import connection_broken
from ats.repositories import ats, ats_links
from tests.integration.transactions import transaction

JOB = {"id": "A1", "name": "Accountant"}
STAGE = {"id": "assessment", "name": "Assessment"}


def test_a_reconnect_keeps_linked_jobs_and_a_disconnect_removes_them(run):
    async def scenario():
        company = uuid.uuid4()
        interview = uuid.uuid4()
        await transaction(ats.connect, company, AtsProvider.WORKABLE, "acme", "sealed-1", "ann")
        connection = await transaction(ats.connection, company, AtsProvider.WORKABLE)
        first = await transaction(
            ats_links.add_link, connection.company_id, connection.id, interview, JOB, STAGE, "ann"
        )
        # The same job twice is refused; one job has one interview.
        again = await transaction(
            ats_links.add_link, connection.company_id, connection.id, interview, JOB, STAGE, "ann"
        )
        await transaction(
            ats.mark_broken,
            connection.id,
            connection_broken(connection.company_id, connection.provider),
        )
        await transaction(ats.connect, company, AtsProvider.WORKABLE, "acme", "sealed-2", "bob")
        reconnected = await transaction(ats.connection, company, AtsProvider.WORKABLE)
        kept = await transaction(ats_links.links, company)
        await transaction(ats.disconnect, company, AtsProvider.WORKABLE, "ann")
        gone = (
            await transaction(ats_links.links, company),
            await transaction(ats.connections, company),
        )
        await transaction(ats.delete_company, company)

        return connection, first, again, reconnected, kept, gone

    connection, first, again, reconnected, kept, gone = run(scenario())

    assert first is not None and again is None
    # A reconnect replaces the key and who connected, and works again, with the same row.
    assert reconnected.id == connection.id
    assert (reconnected.credentials, reconnected.created_by, reconnected.status) == (
        "sealed-2",
        "bob",
        "connected",
    )
    assert [(link.job_name, link.stage_name, provider) for link, provider in kept] == [
        ("Accountant", "Assessment", "workable")
    ]
    assert gone == ([], [])


def test_a_company_only_unlinks_its_own_jobs(run):
    async def scenario():
        mine = uuid.uuid4()
        theirs = uuid.uuid4()
        interview = uuid.uuid4()
        await transaction(ats.connect, mine, AtsProvider.WORKABLE, "acme", "sealed", "ann")
        connection = await transaction(ats.connection, mine, AtsProvider.WORKABLE)
        await transaction(
            ats_links.add_link, connection.company_id, connection.id, interview, JOB, STAGE, "ann"
        )
        [(link, _)] = await transaction(ats_links.links, mine)
        by_them = await transaction(ats_links.remove_link, theirs, link.id, "ann")
        by_me = await transaction(ats_links.remove_link, mine, link.id, "ann")
        left = await transaction(ats_links.links, mine)
        await transaction(ats.delete_company, mine)
        await transaction(ats.delete_company, theirs)

        return by_them, by_me, left

    by_them, by_me, left = run(scenario())

    assert (by_them, by_me, left) == (False, True, [])


def test_a_greenhouse_event_finds_its_linked_job_by_connection_and_job_id(run):
    async def scenario():
        company = uuid.uuid4()
        interview = uuid.uuid4()
        await transaction(ats.connect, company, AtsProvider.GREENHOUSE, "…1234", "sealed", "ann")
        await transaction(ats.connect, company, AtsProvider.WORKABLE, "acme", "sealed", "ann")
        greenhouse = await transaction(ats.connection, company, AtsProvider.GREENHOUSE)
        workable = await transaction(ats.connection, company, AtsProvider.WORKABLE)
        link_id = await transaction(
            ats_links.add_link, greenhouse.company_id, greenhouse.id, interview, JOB, STAGE, "ann"
        )
        found = await transaction(ats_links.link_for_job, greenhouse.id, "A1")
        other_job = await transaction(ats_links.link_for_job, greenhouse.id, "B2")
        other_ats = await transaction(ats_links.link_for_job, workable.id, "A1")
        await transaction(ats.delete_company, company)

        return link_id, found, other_job, other_ats

    link_id, found, other_job, other_ats = run(scenario())

    assert found.id == link_id and found.stage_id == "assessment"
    assert (other_job, other_ats) == (None, None)


def test_new_credentials_replace_only_that_connections(run):
    async def scenario():
        company = uuid.uuid4()
        await transaction(
            ats.connect, company, AtsProvider.TEAMTAILOR, "Acme", "sealed-1", "ann", "5"
        )
        await transaction(ats.connect, company, AtsProvider.GREENHOUSE, "…1234", "sealed-g", "ann")
        connection = await transaction(ats.connection, company, AtsProvider.TEAMTAILOR)
        await transaction(ats.set_credentials, connection.id, "sealed-2")
        found = await transaction(ats.connection, company, AtsProvider.TEAMTAILOR)
        other = await transaction(ats.connection, company, AtsProvider.GREENHOUSE)
        await transaction(ats.delete_company, company)

        return found, other

    found, other = run(scenario())

    assert (found.credentials, found.account, found.member_id) == ("sealed-2", "Acme", "5")
    assert other.credentials == "sealed-g"


def test_an_interviews_links_and_whether_a_connection_has_any(run):
    async def scenario():
        company = uuid.uuid4()
        interview = uuid.uuid4()
        await transaction(ats.connect, company, AtsProvider.WORKABLE, "acme", "sealed", "ann")
        await transaction(ats.connect, company, AtsProvider.TEAMTAILOR, "Acme", "sealed", "ann")
        workable = await transaction(ats.connection, company, AtsProvider.WORKABLE)
        teamtailor = await transaction(ats.connection, company, AtsProvider.TEAMTAILOR)
        link_id = await transaction(
            ats_links.add_link, workable.company_id, workable.id, interview, JOB, STAGE, "ann"
        )
        await transaction(
            ats_links.add_link,
            workable.company_id,
            workable.id,
            uuid.uuid4(),
            {"id": "B2", "name": "Support"},
            STAGE,
            "ann",
        )
        found = await transaction(ats_links.interview_links, interview)
        has = (
            await transaction(ats_links.has_links, workable.id),
            await transaction(ats_links.has_links, teamtailor.id),
        )
        await transaction(ats.delete_company, company)

        return link_id, found, has

    link_id, found, has = run(scenario())

    assert [(link.id, connection.provider) for link, connection in found] == [(link_id, "workable")]
    assert has == (True, False)


def test_only_the_companys_working_atss_are_counted(run):
    async def scenario():
        company, other = uuid.uuid4(), uuid.uuid4()
        await transaction(ats.connect, company, AtsProvider.WORKABLE, "acme", "sealed", "ann")
        await transaction(ats.connect, company, AtsProvider.GREENHOUSE, "acme", "sealed", "ann")
        await transaction(ats.connect, other, AtsProvider.WORKABLE, "beta", "sealed", "bob")
        broken = await transaction(ats.connection, company, AtsProvider.GREENHOUSE)
        await transaction(ats.mark_broken, broken.id, connection_broken(company, broken.provider))
        counted = await transaction(ats.connected_count, company)

        for company_id in (company, other):
            await transaction(ats.delete_company, company_id)

        return counted

    # Workable works; Greenhouse is broken; the other company's isn't counted.
    assert run(scenario()) == 1
