import uuid
from datetime import UTC, datetime

import pytest

from companies.constants.invites import InviteStatus
from companies.integrations import rounds
from companies.main import app
from companies.models.companies import Company, Member
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite
from companies.repositories import candidates, companies, interviews
from tests.unit import fake_candidates
from tests.unit.api.v1.test_candidates import COMPANY_ID, INTERVIEW_ID, INVITE_ID, sign_in


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


def listed_with(client, monkeypatch, url, scores=None, flagged=False):
    """Lists candidates with storage's page in memory; what the page was asked for, and the
    rows returned."""
    sign_in()
    interview = Interview(
        pass_mark=70,
        id=INTERVIEW_ID,
        company_id=COMPANY_ID,
        generation_id=uuid.uuid4(),
        set_id=uuid.uuid4(),
    )
    company = Company(id=COMPANY_ID, name="Arcolabs", created_at=datetime.now(UTC))
    company.members = [
        Member(company_id=COMPANY_ID, user_id="bob", invited_email="bob@example.com", role="owner")
    ]
    invite = CandidateInvite(
        id=INVITE_ID,
        interview_id=INTERVIEW_ID,
        email="ada@example.com",
        token="token-ada",
        status=InviteStatus.FINISHED,
        grade=90,
        flagged=flagged,
        created_at=datetime.now(UTC),
    )
    asked = []

    async def fake_interview(_interview_id):
        return interview

    async def fake_company(_company_id):
        return company

    async def fake_page(interview_id, offset, limit, by_grade, q, filter_by, pass_mark, *synced):
        asked.append((by_grade, q, filter_by, pass_mark))

        return [invite]

    async def fake_scores(invite_ids):
        return scores or {}

    monkeypatch.setattr(interviews, "get", fake_interview)
    monkeypatch.setattr(companies, "get", fake_company)
    monkeypatch.setattr(candidates, "page", fake_page)
    monkeypatch.setattr(rounds, "invite_scores", fake_scores)
    response = client.get(url)

    assert response.status_code == 200

    return asked, response.json()


def test_candidates_are_sorted_newest_first_by_default(client, monkeypatch):
    asked, _ = listed_with(client, monkeypatch, f"/interviews/{INTERVIEW_ID}/candidates")

    assert asked == [(False, "", None, 70)]


def test_candidates_can_be_sorted_by_grade(client, monkeypatch):
    url = f"/interviews/{INTERVIEW_ID}/candidates?sort=grade"
    asked, _ = listed_with(client, monkeypatch, url)

    assert asked == [(True, "", None, 70)]


def test_candidates_can_be_searched_by_email_and_filtered_by_status(client, monkeypatch):
    url = f"/interviews/{INTERVIEW_ID}/candidates?sort=date&q=%20ann%20&status=finished"
    asked, _ = listed_with(client, monkeypatch, url)

    assert asked == [(False, "ann", "finished", 70)]


def test_candidate_filters_list_the_statuses(client):
    response = client.get("/interviews/candidates/filters")

    assert response.status_code == 200
    assert {"finished", "passed", "flagged"} <= set(response.json()["filters"])
    assert "deleted" not in response.json()["filters"]


def test_passed_and_flagged_are_filtered_in_storage_with_the_pass_mark(client, monkeypatch):
    totals = {str(INVITE_ID): {"progress": 100, "grade": 90, "finished": True, "tab_leaves": 2}}
    url = f"/interviews/{INTERVIEW_ID}/candidates?status=flagged"
    asked, rows = listed_with(client, monkeypatch, url, totals)

    assert asked == [(False, "", "flagged", 70)]
    assert [(row["email"], row["passed"], row["tab_leaves"]) for row in rows] == [
        ("ada@example.com", True, 2)
    ]


def test_results_missing_on_finished_invites_are_stored_before_sorting(client, monkeypatch):
    async def unscored(_interview_id):
        return [INVITE_ID]

    monkeypatch.setattr(candidates, "unscored", unscored)
    totals = {str(INVITE_ID): {"progress": 100, "grade": 90, "finished": True, "copies": 1}}
    # The page reads what the backfill stored.
    url = f"/interviews/{INTERVIEW_ID}/candidates?sort=grade"
    listed_with(client, monkeypatch, url, totals, flagged=True)

    assert fake_candidates.SAVED == [(INVITE_ID, 90, True)]
