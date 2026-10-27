import uuid
from datetime import UTC, datetime

import pytest
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User

from app.constants.invites import InviteStatus
from app.helpers.candidates import section_passed
from app.integrations import billing, rounds
from app.main import app
from app.models.companies import Company, Member
from app.models.interviews import Interview
from app.models.invites import CandidateInvite
from app.routers import candidates as candidates_router
from app.storage import candidates, companies, interviews
from app.storage import invites as invite_store
from tests.unit import fake_candidates

COMPANY_ID = uuid.uuid4()
INTERVIEW_ID = uuid.uuid4()
INVITE_ID = uuid.uuid4()


def sign_in():
    app.dependency_overrides[current_user] = lambda: User(
        uid="bob", email="bob@example.com", email_verified=True, name="Bob"
    )


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def no_billing(monkeypatch):
    async def done(_key):
        return None

    monkeypatch.setattr(billing, "charge_candidate", done)
    monkeypatch.setattr(billing, "release_candidate", done)


def test_finished_interview_status(client, monkeypatch):
    sign_in()
    invite = CandidateInvite(
        id=INVITE_ID,
        interview_id=INTERVIEW_ID,
        email="viktor2@gmail.com",
        token="token-1",
        status=InviteStatus.IN_PROCESS,
        created_at=datetime.now(UTC),
    )
    interview = Interview(
        pass_mark=70,
        id=INTERVIEW_ID,
        company_id=COMPANY_ID,
        generation_id=uuid.uuid4(),
        set_id=uuid.uuid4(),
    )
    fake_candidates.add(invite)
    company = Company(id=COMPANY_ID, name="Arcolabs", created_at=datetime.now(UTC))
    company.members = [
        Member(
            company_id=COMPANY_ID,
            user_id="bob",
            invited_email="bob@example.com",
            role="owner",
            created_at=datetime.now(UTC),
        )
    ]

    async def fake_interview(_interview_id):
        return interview

    async def fake_company(_company_id):
        return company

    async def fake_scores(_invite_ids):
        return {str(INVITE_ID): {"progress": 40, "grade": 80, "finished": True}}

    monkeypatch.setattr(interviews, "get", fake_interview)
    monkeypatch.setattr(companies, "get", fake_company)
    monkeypatch.setattr(rounds, "invite_scores", fake_scores)
    asked = []

    async def fake_page(interview_id, offset, limit, by_grade, q, filter_by, pass_mark, *synced):
        asked.append((interview_id, offset, limit, by_grade))

        return [invite]

    monkeypatch.setattr(candidates, "page", fake_page)

    response = client.get(f"/interviews/{INTERVIEW_ID}/candidates?sort=date&offset=20&limit=20")

    assert response.status_code == 200
    assert response.json()[0]["status"] == "finished"
    # Rounds finished it before interview.finished arrived: its results are stored now.
    assert fake_candidates.SAVED == [(INVITE_ID, 80, False)]
    assert asked == [(INTERVIEW_ID, 20, 20, False)]


def revoke(client, monkeypatch, status, progress=0, picked=0, removed_as=None):
    """Revokes the candidate, who is `progress` percent through with `picked` answers chosen
    (the rest timed out) and is `removed_as` (their
    status read, by default) when deleted; what was removed, whose sessions were erased, how
    many credits were released and how many charged."""
    sign_in()
    removed = []
    erased = []
    released = []
    charged = []
    invite = CandidateInvite(
        id=INVITE_ID,
        interview_id=INTERVIEW_ID,
        email="cand@example.com",
        token="token-2",
        status=status,
        created_at=datetime.now(UTC),
    )
    interview = Interview(
        pass_mark=70,
        id=INTERVIEW_ID,
        company_id=COMPANY_ID,
        generation_id=uuid.uuid4(),
        set_id=uuid.uuid4(),
    )
    fake_candidates.add(invite)
    company = Company(id=COMPANY_ID, name="Arcolabs", created_at=datetime.now(UTC))
    company.members = [
        Member(
            company_id=COMPANY_ID,
            user_id="bob",
            invited_email="bob@example.com",
            role="owner",
            created_at=datetime.now(UTC),
        )
    ]

    async def fake_interview(_interview_id):
        return interview

    async def fake_company(_company_id):
        return company

    async def fake_remove(invite, company_id):
        # The other services hear of it with the company and the candidate's email.
        assert company_id == COMPANY_ID
        removed.append(invite.id)

        return removed_as or status

    async def no_flush():
        pass

    async def fake_erase(invite_ids):
        erased.extend(invite_ids)

    async def fake_release(key):
        released.append(key)

    async def fake_charge(key):
        charged.append(key)

    async def fake_scores(invite_ids):
        return {
            str(invite_id): {"progress": progress, "picked": picked} for invite_id in invite_ids
        }

    monkeypatch.setattr(interviews, "get", fake_interview)
    monkeypatch.setattr(companies, "get", fake_company)
    monkeypatch.setattr(invite_store, "remove", fake_remove)
    monkeypatch.setattr(candidates_router.outbox_service, "flush_quietly", no_flush)
    monkeypatch.setattr(rounds, "delete_invite_sessions", fake_erase)
    monkeypatch.setattr(billing, "release_candidate", fake_release)
    monkeypatch.setattr(billing, "charge_candidate", fake_charge)
    monkeypatch.setattr(rounds, "invite_scores", fake_scores)
    response = client.delete(f"/interviews/{INTERVIEW_ID}/candidates/{INVITE_ID}")

    return response.status_code, removed, erased, len(released), len(charged)


def test_an_unused_invite_is_revoked(client, monkeypatch):
    assert revoke(client, monkeypatch, InviteStatus.INVITED) == (204, [INVITE_ID], [], 1, 0)


def test_a_started_candidate_without_an_answer_is_erased_and_their_credits_come_back(
    client, monkeypatch
):
    status = InviteStatus.IN_PROCESS

    assert revoke(client, monkeypatch, status) == (204, [INVITE_ID], [INVITE_ID], 1, 0)


def test_a_started_candidate_who_answered_is_erased_and_charged(client, monkeypatch):
    status = InviteStatus.IN_PROCESS

    assert revoke(client, monkeypatch, status, 10, 1) == (204, [INVITE_ID], [INVITE_ID], 0, 1)


def test_a_started_candidate_whose_questions_only_timed_out_gets_their_credits_back(
    client, monkeypatch
):
    """Half way through, but every question ran out of time: nothing answered, nothing paid, as
    when such a candidate finishes."""
    status = InviteStatus.IN_PROCESS

    assert revoke(client, monkeypatch, status, 50) == (204, [INVITE_ID], [INVITE_ID], 1, 0)


def test_a_candidate_who_started_while_revoked_loses_their_new_sessions(client, monkeypatch):
    status, started = InviteStatus.INVITED, InviteStatus.IN_PROCESS

    assert revoke(client, monkeypatch, status, removed_as=started) == (
        204,
        [INVITE_ID],
        [INVITE_ID],
        1,
        0,
    )


def test_a_finished_candidate_is_erased_and_stays_charged(client, monkeypatch):
    assert revoke(client, monkeypatch, InviteStatus.FINISHED) == (
        204,
        [INVITE_ID],
        [INVITE_ID],
        0,
        0,
    )


def test_a_finished_section_passes_at_the_pass_mark():
    assert section_passed({"status": "finished", "final_score": 70}, 70) is True
    assert section_passed({"status": "finished", "final_score": 69}, 70) is False
    assert section_passed({"status": "in_progress", "final_score": None}, 70) is None
