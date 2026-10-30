import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from prepza_common.auth.service_auth import issue_token
from prepza_common.http.http import bearer

from companies.integrations import rounds
from companies.repositories import candidates, interview_notes, interviews
from companies.services import candidate_results, interview_views

COMPANY_ID, OTHER_ID = uuid.uuid4(), uuid.uuid4()
INTERVIEW = SimpleNamespace(
    id=uuid.uuid4(), company_id=COMPANY_ID, set_id=uuid.uuid4(), pass_mark=70, voice=False
)
INVITE = SimpleNamespace(
    id=uuid.uuid4(),
    email="anna@example.com",
    name="Anna Nowak",
    status="finished",
    token="tok-anna",
    created_at=datetime(2026, 10, 2, tzinfo=UTC),
    flagged=False,
    extra_time=50,
    voice=None,
    started_at=datetime(2026, 10, 3, 9, tzinfo=UTC),
    finished_at=datetime(2026, 10, 3, 9, 20, tzinfo=UTC),
    updated_at=datetime(2026, 10, 3, 9, 20, tzinfo=UTC),
)
TOKEN = issue_token("api", "companies", "test-secret-that-is-at-least-32-bytes")
HEADERS = bearer(TOKEN)
BASE = f"/internal/companies/{COMPANY_ID}/interviews"


@pytest.fixture(autouse=True)
def stored(monkeypatch):
    """The company's one interview with one finished candidate; returns the pages asked for."""
    asked = []

    async def get_interview(session, interview_id):
        return INTERVIEW if interview_id == INTERVIEW.id else None

    async def list_for_company(session, company_id, offset, limit, since=None, after=None):
        asked.append((company_id, offset, limit))

        return [INTERVIEW] if company_id == COMPANY_ID else []

    async def counts(session, ids):
        return {INTERVIEW.id: 1}

    async def notes(session, ids):
        return {INTERVIEW.id: (2, "Strong on SQL")}

    async def interview_out(interview, count=0, notes=(0, None)):
        return {
            "id": interview.id,
            "generation_id": None,
            "set_id": uuid.uuid4(),
            "generation_failed": False,
            "title": "Backend",
            "question_seconds": 60,
            "candidate_count": count,
            "note_count": notes[0],
            "pinned_note": notes[1],
            "hired": False,
            "pass_mark": 70,
            "link_token": None,
            "status": "in_process",
            "created_at": datetime(2026, 10, 1, tzinfo=UTC),
        }

    async def get_candidate(session, interview_id, invite_id):
        return INVITE if invite_id == INVITE.id else None

    async def scores(ids):
        return {str(INVITE.id): {"finished": True, "grade": 86, "progress": 100, "copies": 1}}

    async def scorecard(invite_id):
        # Two sections: one finished, one not.
        return [
            {"topic_title": "SQL", "final_score": 90},
            {"topic_title": "APIs", "final_score": None},
        ]

    async def answer_patterns(invite_id):
        return {"signals": [{"kind": "timing"}], "follow_ups": [{"question_id": "q"}]}

    async def page(
        interview, offset, limit, by_grade, q="", filter_by=None, with_link=False, **synced
    ):
        asked.append(("candidates", offset, limit, by_grade, with_link))

        return []

    monkeypatch.setattr(interviews, "get", get_interview)
    monkeypatch.setattr(interviews, "list_for_company", list_for_company)
    monkeypatch.setattr(candidates, "counts", counts)
    monkeypatch.setattr(interview_notes, "summaries", notes)
    monkeypatch.setattr(candidates, "get", get_candidate)
    monkeypatch.setattr(interview_views, "interview_out", interview_out)
    monkeypatch.setattr(rounds, "invite_scores", scores)
    monkeypatch.setattr(rounds, "scorecard", scorecard)
    monkeypatch.setattr(rounds, "answer_patterns", answer_patterns)
    monkeypatch.setattr(candidate_results, "page", page)

    return asked


def test_the_api_service_lists_a_companys_interviews_a_page_at_a_time(client, stored):
    response = client.get(f"{BASE}?offset=5&limit=10", headers=HEADERS)

    assert response.status_code == 200
    assert [item["candidate_count"] for item in response.json()] == [1]
    assert [(item["note_count"], item["pinned_note"]) for item in response.json()] == [
        (2, "Strong on SQL")
    ]
    assert stored == [(COMPANY_ID, 5, 10)]


def test_an_interview_and_its_candidates_newest_first(client, stored):
    assert client.get(f"{BASE}/{INTERVIEW.id}", headers=HEADERS).status_code == 200
    assert client.get(f"{BASE}/{INTERVIEW.id}/candidates", headers=HEADERS).json() == []
    # With the invite links, for the public API.
    assert stored == [("candidates", 0, 100, False, True)]


def test_a_candidate_comes_with_their_results(client):
    found = client.get(f"{BASE}/{INTERVIEW.id}/candidates/{INVITE.id}", headers=HEADERS).json()

    assert (found["grade"], found["passed"], found["copies"]) == (86, True, 1)
    assert found["name"] == "Anna Nowak"
    assert (found["extra_time"], found["flagged"]) == (50, False)
    assert found["finished_at"] == "2026-10-03T09:20:00Z"
    # One candidate comes with each section's grade.
    assert found["sections"] == [
        {"title": "SQL", "grade": 90},
        {"title": "APIs", "grade": None},
    ]
    # Finished: no invite link.
    assert found["invite_token"] is None
    # The signals its answers and times show, never the questions to ask about; they don't make
    # the candidate flagged (what ATSs and web hooks are told), only the browser's signals do.
    assert [signal["kind"] for signal in found["answer_signals"]] == ["timing"]
    assert "follow_ups" not in found
    assert found["flagged"] is False


def test_a_candidate_who_hasnt_finished_comes_with_their_invite_link(client, monkeypatch):
    monkeypatch.setattr(INVITE, "status", "in_process")
    found = client.get(f"{BASE}/{INTERVIEW.id}/candidates/{INVITE.id}", headers=HEADERS).json()

    assert found["invite_token"] == "tok-anna"


def test_another_companys_interview_or_an_unknown_candidate_is_not_found(client):
    other = f"/internal/companies/{OTHER_ID}/interviews/{INTERVIEW.id}"

    assert client.get(other, headers=HEADERS).status_code == 404
    assert client.get(f"{other}/candidates", headers=HEADERS).status_code == 404
    assert (
        client.get(f"{BASE}/{INTERVIEW.id}/candidates/{uuid.uuid4()}", headers=HEADERS).status_code
        == 404
    )


def test_only_services_may_ask(client):
    assert client.get(BASE).status_code in (401, 403)
