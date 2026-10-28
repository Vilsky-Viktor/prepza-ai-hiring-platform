import asyncio
import uuid
from types import SimpleNamespace

import httpx
import pytest
from prepza_common.events.notifications import notification

from companies.constants.invites import InviteStatus
from companies.integrations import billing, rounds
from companies.repositories import interviews, invite_progress, invites
from companies.services import candidate_billing
from companies.services import outbox as outbox_service

INTERVIEW_ID = uuid.uuid4()


@pytest.fixture
def ledger(monkeypatch):
    calls = []

    async def charge(key):
        calls.append(("charge", key))

    async def release(key):
        calls.append(("release", key))

    monkeypatch.setattr(billing, "charge_candidate", charge)
    monkeypatch.setattr(billing, "release_candidate", release)

    return calls


COMPANY_ID = uuid.uuid4()


def finished(monkeypatch, status=InviteStatus.IN_PROCESS, pass_mark=70):
    """The invite, and the notifications saved as it's finished (its candidate.finished event
    in `invite.result`)."""
    invite = SimpleNamespace(
        id=uuid.uuid4(),
        interview_id=INTERVIEW_ID,
        email="carol@example.com",
        name="Carol Diaz",
        status=status,
        hold_key=f"{INTERVIEW_ID}:carol-key",
    )
    notices = []

    async def fake_get(session, invite_id):
        return invite

    async def fake_finish(session, invite_id, grade, flagged, notice, event_id, result):
        invite.results = (grade, flagged)
        invite.result = result
        notices.append(notice)

    async def fake_interview(session, interview_id):
        return SimpleNamespace(
            id=interview_id,
            company_id=COMPANY_ID,
            title="Backend",
            language="de",
            pass_mark=pass_mark,
        )

    async def fake_scores(invite_ids):
        return {str(invite.id): {"progress": 100, "grade": 85, "finished": True, "copies": 1}}

    async def no_flush():
        pass

    monkeypatch.setattr(invites, "get", fake_get)
    monkeypatch.setattr(invite_progress, "finish", fake_finish)
    monkeypatch.setattr(interviews, "get", fake_interview)
    monkeypatch.setattr(rounds, "invite_scores", fake_scores)
    monkeypatch.setattr(outbox_service, "flush_quietly", no_flush)

    return invite, notices


def test_a_finished_interview_with_an_answer_charges_and_tells_the_company(ledger, monkeypatch):
    invite, notices = finished(monkeypatch)

    asyncio.run(
        candidate_billing.finish({"candidate_invite_id": str(invite.id), "answered": 2}, "event-1")
    )

    assert notices == [
        notification(
            "company",
            COMPANY_ID,
            "candidate_finished",
            f"/companies/{COMPANY_ID}/interviews/{INTERVIEW_ID}",
            # One per invite, however often the event comes.
            key=str(invite.id),
            email="carol@example.com",
            title="Backend",
            # Slack opens the candidate's results from it.
            candidate_link=f"/companies/{COMPANY_ID}/interviews/{INTERVIEW_ID}/candidates/{invite.id}",
            grade=85,
            candidate_name="Carol Diaz",
        )
    ]
    # Stored on the invite, so the candidates list sorts and filters by them.
    assert invite.results == (85, True)
    assert ledger == [("charge", f"{INTERVIEW_ID}:carol-key")]
    # ats writes the result back to the ATS that sent the candidate.
    assert invite.result == {
        "candidate_invite_id": str(invite.id),
        "interview_id": str(INTERVIEW_ID),
        "company_id": str(COMPANY_ID),
        "title": "Backend",
        "language": "de",
        "grade": 85,
        "passed": True,
        "flagged": True,
    }


def test_a_grade_under_the_pass_mark_or_none_hasnt_passed(ledger, monkeypatch):
    invite, _ = finished(monkeypatch, pass_mark=90)
    data = {"candidate_invite_id": str(invite.id), "answered": 2}
    asyncio.run(candidate_billing.finish(data, "event-1"))
    under = invite.result["passed"]

    async def no_grade(invite_ids):
        return {}

    monkeypatch.setattr(rounds, "invite_scores", no_grade)
    asyncio.run(candidate_billing.finish(data, "event-2"))

    assert under is False
    assert (invite.result["grade"], invite.result["passed"]) == (None, False)


def test_rounds_being_down_charges_but_retries_for_the_grade(ledger, monkeypatch):
    """The charge goes through; nothing is sent without the grade, and the event comes again."""
    invite, notices = finished(monkeypatch)
    data = {"candidate_invite_id": str(invite.id), "answered": 2}
    scores = rounds.invite_scores

    async def down(invite_ids):
        raise httpx.ConnectError("rounds is down")

    monkeypatch.setattr(rounds, "invite_scores", down)

    with pytest.raises(httpx.ConnectError):
        asyncio.run(candidate_billing.finish(data, "event-1"))

    assert notices == []
    assert ledger == [("charge", f"{INTERVIEW_ID}:carol-key")]

    # Retried once rounds answers: the company and its ATS get the grade.
    monkeypatch.setattr(rounds, "invite_scores", scores)
    asyncio.run(candidate_billing.finish(data, "event-1"))

    assert notices[0]["data"]["grade"] == 85
    assert invite.result["grade"] == 85
    assert ledger == [("charge", f"{INTERVIEW_ID}:carol-key")] * 2


def test_a_finished_interview_without_an_answer_gives_the_credits_back(ledger, monkeypatch):
    invite, notices = finished(monkeypatch)

    asyncio.run(
        candidate_billing.finish({"candidate_invite_id": str(invite.id), "answered": 0}, "event-1")
    )

    # Finished, but nobody is told.
    assert notices == [None]
    assert ledger == [("release", f"{INTERVIEW_ID}:carol-key")]


def test_a_deleted_candidate_is_left_alone(ledger, monkeypatch):
    invite, notices = finished(monkeypatch, InviteStatus.DELETED)

    asyncio.run(
        candidate_billing.finish({"candidate_invite_id": str(invite.id), "answered": 3}, "event-1")
    )

    assert (notices, ledger) == ([], [])
