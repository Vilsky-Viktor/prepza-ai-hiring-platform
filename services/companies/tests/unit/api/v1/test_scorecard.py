import uuid
from datetime import UTC, datetime

import pytest
from prepza_common.auth.service_auth import issue_token
from prepza_common.events.audit_actions import AuditAction, TargetKind

from companies.constants.invites import InviteStatus
from companies.integrations import rounds
from companies.main import app
from companies.models.companies import Company, Member
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite
from companies.repositories import companies, interviews
from companies.services import scorecards
from tests.unit import fake_candidates
from tests.unit.api.v1.test_candidates import COMPANY_ID, INTERVIEW_ID, INVITE_ID, sign_in

URL = f"/interviews/{INTERVIEW_ID}/candidates/{INVITE_ID}"
SECRET = "test-secret-that-is-at-least-32-bytes"
# A section as rounds returns it: one answered question.
SECTION = {
    "id": str(uuid.uuid4()),
    "topic_title": "Python",
    "status": "finished",
    "final_score": 80,
    "tab_leaves": 1,
    "copies": 0,
    "fast_answers": 0,
    "review": [
        {
            "question_id": str(uuid.uuid4()),
            "number": 1,
            "text": "What does len([]) return?",
            "options": ["0", "None"],
            "multi": False,
            # The question's own time, which the report shows the answer's time against.
            "limit_seconds": 49,
            "correct_option_index": 0,
            "correct_indexes": [0],
            "answer": {
                "answer_id": str(uuid.uuid4()),
                "option_index": 0,
                "picks": [0],
                "timed_out": False,
                "right_picks": 1,
                "wrong_picks": 0,
                "correct": True,
                "score": 100,
                "seconds": 12,
                "fast": False,
            },
            "tab_leaves": 1,
            "copies": 0,
        }
    ],
}


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def tracked(monkeypatch):
    """The funnel events sent, by name."""
    events = []

    async def track(name, **kwargs):
        events.append(name)

    monkeypatch.setattr(scorecards, "track", track)

    return events


PLEDGED_AT = datetime(2026, 10, 21, 9, 30, tzinfo=UTC)
# What rounds finds in the answers and times: a signal, and a question to ask about.
PATTERNS = {
    "signals": [{"kind": "person_fit", "hard": 5, "hard_right": 5, "easy": 5, "easy_wrong": 3}],
    "follow_ups": [
        {
            "question_id": SECTION["review"][0]["question_id"],
            "topic_title": "Python",
            "text": "What does len([]) return?",
            "right": ["0"],
            "wrong": "None",
        }
    ],
}


def open_scorecard(
    client,
    monkeypatch,
    headers=None,
    status=InviteStatus.FINISHED,
    role="owner",
    language="ar",
    own=None,
):
    sign_in()
    fake_candidates.add(
        CandidateInvite(
            id=INVITE_ID,
            interview_id=INTERVIEW_ID,
            email="ann@example.com",
            name="Ann Lee",
            token="token-ann",
            status=status,
            extra_time=0,
            created_at=datetime.now(UTC),
            pledged_at=PLEDGED_AT if status == InviteStatus.FINISHED else None,
            voice=own,
        )
    )
    interview = Interview(
        id=INTERVIEW_ID,
        company_id=COMPANY_ID,
        generation_id=uuid.uuid4(),
        set_id=uuid.uuid4(),
        title="Backend",
        pass_mark=70,
        language=language,
        voice=False,
    )
    company = Company(id=COMPANY_ID, name="Arcolabs", created_at=datetime.now(UTC))
    company.members = [
        Member(company_id=COMPANY_ID, user_id="bob", invited_email="bob@example.com", role=role)
    ]

    async def fake_interview(session, _interview_id):
        return interview

    async def fake_company(session, _company_id):
        return company

    started = status == InviteStatus.FINISHED

    async def fake_scorecard(_invite_id):
        return [SECTION] if started else []

    async def fake_scores(_invite_ids):
        return {str(INVITE_ID): {"progress": 100, "grade": 80, "finished": True}} if started else {}

    async def fake_patterns(_invite_id):
        return PATTERNS if started else {"signals": [], "follow_ups": []}

    monkeypatch.setattr(interviews, "get", fake_interview)
    monkeypatch.setattr(companies, "get", fake_company)
    monkeypatch.setattr(rounds, "scorecard", fake_scorecard)
    monkeypatch.setattr(rounds, "invite_scores", fake_scores)
    monkeypatch.setattr(rounds, "answer_patterns", fake_patterns)

    return client.get(URL, headers=headers or {})


def test_the_scorecard_carries_the_overall_result_for_the_pdf(client, monkeypatch, tracked):
    response = open_scorecard(client, monkeypatch)
    card = response.json()

    assert response.status_code == 200
    assert (card["title"], card["company"], card["grade"], card["passed"]) == (
        "Backend",
        "Arcolabs",
        80,
        True,
    )
    assert card["sessions"] == [{**SECTION, "passed": True}]
    assert card["name"] == "Ann Lee"
    # When they pledged to answer on their own, for the report's line.
    assert datetime.fromisoformat(card["pledged_at"]) == PLEDGED_AT
    # The questions' language, which the page marks them with (lang, dir).
    assert card["language"] == "ar"
    # What the answers and times show, as rounds found it.
    assert card["answer_patterns"] == PATTERNS


@pytest.mark.parametrize(
    ("status", "role", "token"),
    [
        (InviteStatus.INVITED, "owner", "token-ann"),
        (InviteStatus.UNDELIVERED, "admin", "token-ann"),
        (InviteStatus.IN_PROCESS, "owner", "token-ann"),
        # The link no longer works, or the interview is over.
        (InviteStatus.EXPIRED, "owner", None),
        (InviteStatus.FINISHED, "owner", None),
        # A viewer doesn't send invites.
        (InviteStatus.INVITED, "viewer", None),
    ],
)
def test_the_invite_link_is_there_to_copy_until_the_candidate_finishes(
    client, monkeypatch, tracked, status, role, token
):
    card = open_scorecard(client, monkeypatch, status=status, role=role).json()

    assert card["invite_token"] == token


@pytest.mark.parametrize(
    ("status", "role", "language", "editable"),
    [
        (InviteStatus.INVITED, "owner", "en", True),
        (InviteStatus.EXPIRED, "admin", "de", True),
        # Started: their sessions are made in their mode.
        (InviteStatus.IN_PROCESS, "owner", "en", False),
        (InviteStatus.FINISHED, "owner", "en", False),
        # A viewer changes nothing; voice mode doesn't speak Arabic.
        (InviteStatus.INVITED, "viewer", "en", False),
        (InviteStatus.INVITED, "owner", "ar", False),
    ],
)
def test_a_candidates_mode_can_be_changed_until_they_start(
    client, monkeypatch, tracked, status, role, language, editable
):
    card = open_scorecard(
        client, monkeypatch, status=status, role=role, language=language, own=True
    ).json()

    # Their own mode, apart from the interview's click mode.
    assert card["voice"] is True
    assert card["mode_editable"] is editable


def test_viewing_a_finished_candidates_results_is_recorded(client, monkeypatch, audited, tracked):
    assert open_scorecard(client, monkeypatch).status_code == 200
    assert audited == [
        (COMPANY_ID, "bob", AuditAction.RESULTS_VIEWED, INVITE_ID, TargetKind.CANDIDATE)
    ]
    assert tracked == ["results_viewed"]


@pytest.mark.parametrize("via", ["assistant", "mcp"])
def test_a_read_through_the_assistant_or_an_ai_app_is_recorded_as_such_and_not_in_the_funnel(
    client, monkeypatch, audited, tracked, via
):
    token = issue_token(via, "companies", SECRET)

    assert open_scorecard(client, monkeypatch, {"X-Assistant": token}).status_code == 200
    assert audited == [
        (COMPANY_ID, "bob", AuditAction.RESULTS_VIEWED, INVITE_ID, TargetKind.CANDIDATE, via)
    ]
    assert tracked == []


@pytest.mark.parametrize(
    "token",
    [
        "forged",
        # Signed with another key, or by another service.
        issue_token("assistant", "companies", "another-secret-that-is-at-least-32-bytes"),
        issue_token("rounds", "companies", SECRET),
        issue_token("assistant", "rounds", SECRET),
    ],
    ids=["not a token", "wrong key", "another service", "for another service"],
)
def test_a_forged_assistant_header_is_ignored(client, monkeypatch, audited, tracked, token):
    assert open_scorecard(client, monkeypatch, {"X-Assistant": token}).status_code == 200
    assert audited == [
        (COMPANY_ID, "bob", AuditAction.RESULTS_VIEWED, INVITE_ID, TargetKind.CANDIDATE)
    ]
    assert tracked == ["results_viewed"]


def test_the_assistant_header_is_not_in_the_api_description():
    route = app.openapi()["paths"]["/interviews/{interview_id}/candidates/{invite_id}"]
    parameters = route["get"]["parameters"]

    assert [parameter["name"] for parameter in parameters] == ["interview_id", "invite_id"]
