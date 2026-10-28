import uuid

from ats.constants.ats import AtsProvider, CandidateStatus
from ats.helpers.notifications import connection_broken
from ats.repositories import ats, ats_candidates, ats_links, ats_results
from tests.integration.transactions import transaction

JOB = {"id": "A1", "name": "Accountant"}
STAGE = {"id": "assessment", "name": "Assessment"}


def test_the_recovery_job_finds_waiting_candidates_of_working_connections_oldest_first(run):
    async def scenario():
        company = uuid.uuid4()
        interview = uuid.uuid4()
        await transaction(ats.connect, company, AtsProvider.WORKABLE, "acme", "sealed", "ann")
        await transaction(ats.connect, company, AtsProvider.GREENHOUSE, "", "sealed", "ann")
        working = await transaction(ats.connection, company, AtsProvider.WORKABLE)
        broken = await transaction(ats.connection, company, AtsProvider.GREENHOUSE)
        await transaction(
            ats.mark_broken, broken.id, connection_broken(broken.company_id, broken.provider)
        )
        await transaction(ats_candidates.add, working.id, None, interview, "first", "a@x.com")
        await transaction(ats_candidates.add, working.id, None, interview, "second", "b@x.com")
        await transaction(ats_candidates.add, broken.id, None, interview, "broken", "c@x.com")
        invited = await transaction(
            ats_candidates.add, working.id, None, interview, "invited", "d@x.com"
        )
        await transaction(
            ats_candidates.settle, invited.id, CandidateStatus.INVITED, invite_id=uuid.uuid4()
        )
        found = [row.candidate_id for row in await transaction(ats_candidates.recoverable)]
        await transaction(ats.delete_company, company)

        return found

    found = run(scenario())

    assert [item for item in found if item in ("first", "second", "broken", "invited")] == [
        "first",
        "second",
    ]


def test_an_invite_failed_in_passing_waits_with_one_attempt_more(run):
    async def scenario():
        company = uuid.uuid4()
        await transaction(ats.connect, company, AtsProvider.WORKABLE, "acme", "sealed", "ann")
        connection = await transaction(ats.connection, company, AtsProvider.WORKABLE)
        row = await transaction(
            ats_candidates.add, connection.id, None, uuid.uuid4(), "c-1", "a@x.com"
        )
        await transaction(ats_candidates.claim, row.id, (CandidateStatus.WAITING,))
        await transaction(ats_candidates.postpone, row.id)
        await transaction(ats_candidates.claim, row.id, (CandidateStatus.WAITING,))
        await transaction(ats_candidates.postpone, row.id)
        found = [
            item for item in await transaction(ats_candidates.recoverable) if item.id == row.id
        ]
        await transaction(ats.delete_company, company)

        return found

    [found] = run(scenario())

    assert (found.status, found.attempts) == ("waiting", 2)


def test_results_kept_while_broken_are_found_once_reconnected_and_sent_once(run):
    async def scenario():
        company = uuid.uuid4()
        invite = uuid.uuid4()
        await transaction(
            ats.connect, company, AtsProvider.WORKABLE, "acme", "sealed-1", "ann", "m-1"
        )
        connection = await transaction(ats.connection, company, AtsProvider.WORKABLE)
        row = await transaction(
            ats_candidates.add, connection.id, None, uuid.uuid4(), "c-1", "a@x.com"
        )
        await transaction(ats_candidates.settle, row.id, CandidateStatus.INVITED, invite_id=invite)
        await transaction(
            ats.mark_broken,
            connection.id,
            connection_broken(connection.company_id, connection.provider),
        )
        await transaction(ats_results.keep, row.id, {"candidate_invite_id": str(invite)})
        results = [await transaction(ats_results.unreported)]
        await transaction(
            ats.connect, company, AtsProvider.WORKABLE, "acme", "sealed-2", "ann", "m-1"
        )
        results.append(await transaction(ats_results.unreported))
        await transaction(ats_results.mark_reported, row.id)
        results.append(await transaction(ats_results.unreported))
        await transaction(ats.delete_company, company)
        mine = [[item.result for item in found if item.id == row.id] for found in results]

        return invite, mine

    invite, (while_broken, reconnected, after) = run(scenario())

    assert while_broken == [] and after == []
    assert reconnected == [{"candidate_invite_id": str(invite)}]


def test_results_an_ats_keeps_refusing_go_to_the_back_of_the_line(run):
    async def scenario():
        company = uuid.uuid4()
        await transaction(
            ats.connect, company, AtsProvider.WORKABLE, "acme", "sealed", "ann", "m-1"
        )
        connection = await transaction(ats.connection, company, AtsProvider.WORKABLE)
        rows = [
            await transaction(
                ats_candidates.add, connection.id, None, uuid.uuid4(), name, f"{name}@x.com"
            )
            for name in ("first", "second")
        ]

        for row in rows:
            await transaction(ats_results.keep, row.id, {"name": row.candidate_id})

        # The first one's ATS refused it again: kept again, so it's tried after the second.
        await transaction(ats_results.keep, rows[0].id, {"name": "first"})
        found = [
            item.candidate_id
            for item in await transaction(ats_results.unreported)
            if item.connection_id == connection.id
        ]
        await transaction(ats.delete_company, company)

        return found

    assert run(scenario()) == ["second", "first"]


def test_a_failed_reconnect_puts_the_earlier_connection_back_marked_broken(run):
    async def scenario():
        company = uuid.uuid4()
        interview = uuid.uuid4()
        await transaction(
            ats.connect, company, AtsProvider.BREEZY, "Acme", "sealed-1", "ann", "m-1"
        )
        earlier = await transaction(ats.connection, company, AtsProvider.BREEZY)
        await transaction(
            ats_links.add_link, earlier.company_id, earlier.id, interview, JOB, STAGE, "ann"
        )
        await transaction(ats.connect, company, AtsProvider.BREEZY, "Other", "sealed-2", "bob")
        await transaction(ats.restore_broken, earlier)
        found = await transaction(ats.connection, company, AtsProvider.BREEZY)
        links = await transaction(ats_links.links, company)
        await transaction(ats.delete_company, company)

        return earlier, found, links

    earlier, found, links = run(scenario())

    assert found.id == earlier.id
    assert (found.account, found.credentials, found.created_by, found.member_id) == (
        "Acme",
        "sealed-1",
        "ann",
        "m-1",
    )
    assert found.status == "broken"
    assert len(links) == 1


def test_an_unlinked_jobs_waiting_candidates_are_never_invited(run):
    """They'd be invited, with credits set aside, for a job the page no longer shows."""

    async def scenario():
        company = uuid.uuid4()
        interview = uuid.uuid4()
        await transaction(ats.connect, company, AtsProvider.WORKABLE, "acme", "sealed", "ann")
        connection = await transaction(ats.connection, company, AtsProvider.WORKABLE)
        link_id = await transaction(
            ats_links.add_link, connection.company_id, connection.id, interview, JOB, STAGE, "ann"
        )
        await transaction(
            ats_candidates.add, connection.id, link_id, interview, "unlinked-wait", "w@x.com"
        )
        invited = await transaction(
            ats_candidates.add, connection.id, link_id, interview, "unlinked-done", "d@x.com"
        )
        invite_id = uuid.uuid4()
        await transaction(
            ats_candidates.settle, invited.id, CandidateStatus.INVITED, invite_id=invite_id
        )
        await transaction(ats_links.remove_link, company, link_id, "ann")
        found = (
            [row.candidate_id for row in await transaction(ats_candidates.recoverable)],
            [row.candidate_id for row in await transaction(ats_candidates.waiting, interview)],
            await transaction(ats_results.for_invite, invite_id),
        )
        await transaction(ats.delete_company, company)

        return found

    recoverable, waiting, kept = run(scenario())

    assert "unlinked-wait" not in recoverable
    assert waiting == []
    # Invited ones stay, for writing their results back.
    assert kept is not None and kept[0].status == CandidateStatus.INVITED


def test_the_recovery_job_takes_each_connections_candidates_in_turn(run):
    """One company's backlog doesn't hold up another's: every connection's oldest comes first."""

    async def scenario():
        busy, quiet = uuid.uuid4(), uuid.uuid4()
        interview = uuid.uuid4()
        await transaction(ats.connect, busy, AtsProvider.WORKABLE, "busy", "sealed", "ann")
        await transaction(ats.connect, quiet, AtsProvider.WORKABLE, "quiet", "sealed", "bob")
        backlog = await transaction(ats.connection, busy, AtsProvider.WORKABLE)
        other = await transaction(ats.connection, quiet, AtsProvider.WORKABLE)
        ours = []

        for name in ("busy-1", "busy-2", "busy-3"):
            ours.append(name)
            await transaction(
                ats_candidates.add, backlog.id, None, interview, name, f"{name}@x.com"
            )

        ours.append("quiet-1")
        await transaction(ats_candidates.add, other.id, None, interview, "quiet-1", "quiet-1@x.com")
        found = [row.candidate_id for row in await transaction(ats_candidates.recoverable)]
        await transaction(ats.delete_company, busy)
        await transaction(ats.delete_company, quiet)

        return [item for item in found if item in ours]

    assert run(scenario()) == ["busy-1", "quiet-1", "busy-2", "busy-3"]
