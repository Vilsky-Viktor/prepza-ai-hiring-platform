"""Connections and linked jobs: connect, reconnect, credentials, links and unlinking."""

import uuid

from app.constants.ats import AtsProvider
from app.storage import ats, ats_links

JOB = {"id": "A1", "name": "Accountant"}
STAGE = {"id": "assessment", "name": "Assessment"}


def test_a_reconnect_keeps_linked_jobs_and_a_disconnect_removes_them(run):
    async def scenario():
        company = uuid.uuid4()
        interview = uuid.uuid4()
        await ats.connect(company, AtsProvider.WORKABLE, "acme", "sealed-1", "ann")
        connection = await ats.connection(company, AtsProvider.WORKABLE)
        first = await ats_links.add_link(
            connection.company_id, connection.id, interview, JOB, STAGE, "ann"
        )
        # The same job twice is refused; one job has one interview.
        again = await ats_links.add_link(
            connection.company_id, connection.id, interview, JOB, STAGE, "ann"
        )
        await ats.mark_broken(connection.id)
        await ats.connect(company, AtsProvider.WORKABLE, "acme", "sealed-2", "bob")
        reconnected = await ats.connection(company, AtsProvider.WORKABLE)
        kept = await ats_links.links(company)
        await ats.disconnect(company, AtsProvider.WORKABLE, "ann")
        gone = await ats_links.links(company), await ats.connections(company)
        await ats.delete_company(company)

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
        await ats.connect(mine, AtsProvider.WORKABLE, "acme", "sealed", "ann")
        connection = await ats.connection(mine, AtsProvider.WORKABLE)
        await ats_links.add_link(connection.company_id, connection.id, interview, JOB, STAGE, "ann")
        [(link, _)] = await ats_links.links(mine)
        by_them = await ats_links.remove_link(theirs, link.id, "ann")
        by_me = await ats_links.remove_link(mine, link.id, "ann")
        left = await ats_links.links(mine)
        await ats.delete_company(mine)
        await ats.delete_company(theirs)

        return by_them, by_me, left

    by_them, by_me, left = run(scenario())

    assert (by_them, by_me, left) == (False, True, [])


def test_a_greenhouse_event_finds_its_linked_job_by_connection_and_job_id(run):
    async def scenario():
        company = uuid.uuid4()
        interview = uuid.uuid4()
        await ats.connect(company, AtsProvider.GREENHOUSE, "…1234", "sealed", "ann")
        await ats.connect(company, AtsProvider.WORKABLE, "acme", "sealed", "ann")
        greenhouse = await ats.connection(company, AtsProvider.GREENHOUSE)
        workable = await ats.connection(company, AtsProvider.WORKABLE)
        link_id = await ats_links.add_link(
            greenhouse.company_id, greenhouse.id, interview, JOB, STAGE, "ann"
        )
        found = await ats_links.link_for_job(greenhouse.id, "A1")
        other_job = await ats_links.link_for_job(greenhouse.id, "B2")
        other_ats = await ats_links.link_for_job(workable.id, "A1")
        await ats.delete_company(company)

        return link_id, found, other_job, other_ats

    link_id, found, other_job, other_ats = run(scenario())

    assert found.id == link_id and found.stage_id == "assessment"
    assert (other_job, other_ats) == (None, None)


def test_new_credentials_replace_only_that_connections(run):
    async def scenario():
        company = uuid.uuid4()
        await ats.connect(company, AtsProvider.TEAMTAILOR, "Acme", "sealed-1", "ann", "5")
        await ats.connect(company, AtsProvider.GREENHOUSE, "…1234", "sealed-g", "ann")
        connection = await ats.connection(company, AtsProvider.TEAMTAILOR)
        await ats.set_credentials(connection.id, "sealed-2")
        found = await ats.connection(company, AtsProvider.TEAMTAILOR)
        other = await ats.connection(company, AtsProvider.GREENHOUSE)
        await ats.delete_company(company)

        return found, other

    found, other = run(scenario())

    assert (found.credentials, found.account, found.member_id) == ("sealed-2", "Acme", "5")
    assert other.credentials == "sealed-g"


def test_an_interviews_links_and_whether_a_connection_has_any(run):
    async def scenario():
        company = uuid.uuid4()
        interview = uuid.uuid4()
        await ats.connect(company, AtsProvider.WORKABLE, "acme", "sealed", "ann")
        await ats.connect(company, AtsProvider.TEAMTAILOR, "Acme", "sealed", "ann")
        workable = await ats.connection(company, AtsProvider.WORKABLE)
        teamtailor = await ats.connection(company, AtsProvider.TEAMTAILOR)
        link_id = await ats_links.add_link(
            workable.company_id, workable.id, interview, JOB, STAGE, "ann"
        )
        await ats_links.add_link(
            workable.company_id,
            workable.id,
            uuid.uuid4(),
            {"id": "B2", "name": "Support"},
            STAGE,
            "ann",
        )
        found = await ats_links.interview_links(interview)
        has = await ats_links.has_links(workable.id), await ats_links.has_links(teamtailor.id)
        await ats.delete_company(company)

        return link_id, found, has

    link_id, found, has = run(scenario())

    assert [(link.id, connection.provider) for link, connection in found] == [(link_id, "workable")]
    assert has == (True, False)
