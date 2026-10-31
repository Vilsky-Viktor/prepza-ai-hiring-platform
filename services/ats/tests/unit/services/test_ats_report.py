import asyncio
import uuid
from datetime import UTC, datetime

import httpx
import pytest
from fastapi import HTTPException, status

from ats.integrations import greenhouse, workable
from ats.integrations.errors import KeyRejected
from ats.models.ats import AtsCandidate, AtsConnection
from ats.repositories import ats, ats_results
from ats.services import ats as integrations
from ats.services import ats_candidates as flow
from ats.services import reports
from ats.templates.comments import COMMENTS

INTERVIEW_ID = uuid.uuid4()
COMPANY_ID = uuid.uuid4()
KEYS = {
    "workable": {"subdomain": "acme", "token": "account-token"},
    "greenhouse": {"client_id": "id", "client_secret": "secret", "webhook_secret": "s"},
}


@pytest.fixture
def finished(monkeypatch):
    """A candidate the ATS sent who finished with 82%, and comments (Workable) or notes
    (Greenhouse) recorded instead of sent. The connection is Workable's, with a member. A claim
    holds until the results are kept, as in the database."""
    connection = AtsConnection(
        id=uuid.uuid4(),
        company_id=COMPANY_ID,
        provider="workable",
        status="connected",
        member_id="m-1",
    )
    row = AtsCandidate(id=uuid.uuid4(), candidate_id="c-1", invite_id=uuid.uuid4())
    state = {
        "comments": [],
        "reported": [],
        "broken": [],
        "kept": [],
        "refused": [],
        "writes_again": [],
        "claimed": set(),
        "fail": None,
        "row": row,
    }

    async def for_invite(session, invite_id):
        return (row, connection) if invite_id == row.invite_id else None

    async def key(found):
        return KEYS[found.provider]

    async def comment(candidate_id, member, text, **credentials):
        # A slow ATS: a second event can arrive meanwhile.
        await asyncio.sleep(0)

        if state["fail"]:
            raise state["fail"]

        state["comments"].append((candidate_id, member, text))

    async def claim_report(session, row_id, data):
        if row_id in state["claimed"]:
            return False

        state["claimed"].add(row_id)

        return True

    async def mark_reported(session, row_id):
        state["reported"].append(row_id)

    async def mark_broken(session, connection_id, notice):
        state["broken"].append(connection_id)

    async def keep_result(session, row_id, data):
        state["claimed"].discard(row_id)
        state["kept"].append((row_id, data))

    monkeypatch.setattr(ats_results, "for_invite", for_invite)
    monkeypatch.setattr(ats_results, "claim", claim_report)
    monkeypatch.setattr(ats_results, "mark_reported", mark_reported)
    monkeypatch.setattr(ats_results, "keep", keep_result)

    async def refuse_writes(session, connection_id, notice):
        state["refused"].append(notice)

    async def writes_again(session, connection_id):
        state["writes_again"].append(connection_id)

    async def no_flush():
        pass

    monkeypatch.setattr(ats, "mark_broken", mark_broken)
    monkeypatch.setattr(ats, "refuse_writes", refuse_writes)
    monkeypatch.setattr(ats, "writes_again", writes_again)
    monkeypatch.setattr(flow.outbox_service, "flush_quietly", no_flush)
    monkeypatch.setattr(integrations, "credentials", key)
    monkeypatch.setattr(workable, "comment", comment)
    monkeypatch.setattr(greenhouse, "comment", comment)

    return state, connection


def result(invite_id, grade=82, passed=True) -> dict:
    """Companies' candidate.finished event, as it carries the result."""
    return {
        "candidate_invite_id": str(invite_id),
        "interview_id": str(INTERVIEW_ID),
        "company_id": str(COMPANY_ID),
        "title": "Accountant",
        "grade": grade,
        "passed": passed,
        "flagged": False,
    }


def report(invite_id, grade=82, passed=True):
    asyncio.run(reports.report(result(invite_id, grade, passed)))


def test_results_go_back_to_workable_once_as_a_comment(finished):
    state, _ = finished
    report(state["row"].invite_id)

    [(candidate_id, member, text)] = state["comments"]
    assert (candidate_id, member) == ("c-1", "m-1")
    assert "testee: Accountant" in text
    assert "Grade: 82% (passed)" in text
    assert text.endswith(
        f"http://localhost:8090/companies/{COMPANY_ID}/interviews/{INTERVIEW_ID}"
        f"/candidates/{state['row'].invite_id}"
    )
    assert state["reported"] == [state["row"].id]


def test_results_are_written_in_the_language_of_the_interview(finished):
    state, _ = finished
    asyncio.run(reports.report({**result(state["row"].invite_id), "language": "de"}))

    [(_, _, text)] = state["comments"]
    assert "Ergebnis: 82 % (bestanden)" in text
    assert "Grade" not in text


def test_results_are_written_in_the_language_of_whoever_connected_the_ats(finished):
    state, connection = finished
    connection.language = "uk"
    asyncio.run(reports.report({**result(state["row"].invite_id), "language": "de"}))

    [(_, _, text)] = state["comments"]
    assert COMMENTS["uk"]["decide"] in text


def test_a_candidate_no_ats_sent_is_ignored(finished):
    state, _ = finished
    report(uuid.uuid4())

    assert state["comments"] == [] and state["reported"] == []


def test_without_a_workable_member_nothing_goes_back(finished):
    state, connection = finished
    connection.member_id = None
    report(state["row"].invite_id)

    assert state["comments"] == []
    # Given up, so the recovery job doesn't try it again and again.
    assert state["reported"] == [state["row"].id]


@pytest.mark.parametrize(
    "failure",
    [HTTPException(status.HTTP_502_BAD_GATEWAY, "down"), httpx.ReadTimeout("no answer")],
)
def test_a_failing_ats_keeps_the_results_for_the_recovery_job_and_the_event_is_done(
    finished, failure
):
    state, _ = finished
    state["fail"] = failure

    # No error: Pub/Sub doesn't send the event again for one company's ATS.
    report(state["row"].invite_id)

    assert state["reported"] == []
    assert [row_id for row_id, _ in state["kept"]] == [state["row"].id]


def reads(monkeypatch, works: bool):
    """Whether Workable still takes the key for reading, as asked after a refused write."""

    async def check(**credentials):
        if not works:
            raise KeyRejected

    monkeypatch.setattr(workable, "check", check)


def test_a_refused_key_marks_the_connection_broken_and_keeps_the_results(finished, monkeypatch):
    state, _ = finished
    state["fail"] = KeyRejected()
    reads(monkeypatch, works=False)
    report(state["row"].invite_id)

    assert len(state["broken"]) == 1
    assert state["reported"] == []
    # Sent once it's reconnected, by the recovery job.
    assert state["kept"] == [(state["row"].id, result(state["row"].invite_id))]


def test_a_key_that_reads_but_cannot_write_keeps_the_results_and_the_connection(
    finished, monkeypatch
):
    """Without write access, not revoked: the connection keeps inviting candidates."""
    state, _ = finished
    state["fail"] = KeyRejected()
    reads(monkeypatch, works=True)
    report(state["row"].invite_id)

    assert state["broken"] == []
    assert state["reported"] == []
    assert state["kept"] == [(state["row"].id, result(state["row"].invite_id))]
    # The company hears of it (storage sends it once per connection), on Workable's page.
    [notice] = state["refused"]
    assert (notice["kind"], notice["data"]["ats"]) == ("ats_cannot_write", "Workable")
    assert notice["link"].endswith("/workable")


def test_a_write_that_goes_through_again_lets_a_later_refusal_be_told(finished):
    state, connection = finished
    connection.write_refused_at = datetime.now(UTC)
    report(state["row"].invite_id)

    assert state["writes_again"] == [connection.id]
    assert state["reported"] == [state["row"].id]


def test_a_broken_connection_keeps_the_results_without_calling_the_ats(finished):
    state, connection = finished
    connection.status = "broken"
    report(state["row"].invite_id)

    assert state["comments"] == [] and state["reported"] == []
    assert state["kept"] == [(state["row"].id, result(state["row"].invite_id))]


def test_a_candidate_gone_from_the_ats_is_given_up_alone(finished):
    state, _ = finished
    state["fail"] = HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    report(state["row"].invite_id)

    assert state["reported"] == [state["row"].id]
    assert state["broken"] == [] and state["kept"] == []


def test_results_go_back_to_greenhouse_as_a_note_without_a_member(finished):
    state, connection = finished
    connection.provider, connection.member_id = "greenhouse", None
    report(state["row"].invite_id, grade=None, passed=False)

    [(candidate_id, member, text)] = state["comments"]
    assert (candidate_id, member) == ("c-1", None)
    assert "the grade is on the scorecard" in text
    assert state["reported"] == [state["row"].id]


def test_two_events_at_once_write_the_results_once(finished):
    state, _ = finished
    data = result(state["row"].invite_id)

    async def both():
        await asyncio.gather(reports.report(data), reports.report(data))

    asyncio.run(both())

    assert len(state["comments"]) == 1
    assert state["reported"] == [state["row"].id]


@pytest.mark.parametrize("failure", [HTTPException(status.HTTP_502_BAD_GATEWAY), ValueError()])
def test_results_that_couldnt_go_back_are_freed_for_the_recovery_job(finished, failure):
    state, _ = finished
    state["fail"] = failure
    report(state["row"].invite_id)
    state["fail"] = None
    report(state["row"].invite_id)

    assert len(state["comments"]) == 1
    assert state["reported"] == [state["row"].id]
