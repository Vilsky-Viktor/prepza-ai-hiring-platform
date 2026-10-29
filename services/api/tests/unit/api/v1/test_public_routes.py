import uuid

import pytest

from api.helpers.public import candidate_of
from tests.unit.api_keys import call
from tests.unit.conftest import CANDIDATE, COMPANY, INTERVIEW, candidate


def test_a_key_lists_its_companys_interviews_and_notes_its_use(client, companies_api, key, stored):
    response = call(client, "GET", "/interviews")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": str(INTERVIEW),
            "title": "Backend",
            "status": "in_process",
            "ready": True,
            "pass_mark": 70,
            "candidate_count": 1,
            "created_at": "2026-10-01T09:00:00Z",
            "updated_at": None,
        }
    ]
    assert stored["used"] == [key.id]


def test_a_candidate_comes_with_signals_and_a_link_to_their_results(client, companies_api, key):
    found = call(client, "GET", f"/interviews/{INTERVIEW}/candidates/{CANDIDATE}").json()

    assert found["signals"] == {
        "tab_leaves": 0,
        "copies": 1,
        "fast_answers": 0,
        # Patterns come only with one candidate that companies read with them.
        "answer_patterns": None,
    }
    assert found["results_url"] == (
        f"http://localhost:8090/companies/{COMPANY}/interviews/{INTERVIEW}/candidates/{CANDIDATE}"
    )
    assert "tab_leaves" not in found
    # Finished: the invite link no longer leads anywhere.
    assert found["invite_url"] is None


def test_one_candidate_comes_with_the_patterns_in_their_answers_by_name():
    found = candidate_of(
        candidate(answer_signals=[{"kind": "timing"}, {"kind": "person_fit", "hard": 4}]),
        COMPANY,
        INTERVIEW,
        "https://prepza.ai",
    )

    assert found.signals.answer_patterns == ["timing", "person_fit"]


def test_a_candidate_who_hasnt_finished_comes_with_their_invite_link():
    found = candidate_of(
        candidate(status="invited", invite_token="tok"), COMPANY, INTERVIEW, "https://prepza.ai"
    )

    assert found.invite_url == "https://prepza.ai/invite/tok"


def test_an_invite_goes_out_as_the_keys_creator(client, companies_api, key):
    response = call(
        client, "POST", f"/interviews/{INTERVIEW}/candidates", json={"email": "bob@example.com"}
    )

    assert response.status_code == 201
    assert companies_api["sent"] == [(INTERVIEW, "bob@example.com", "u1")]


def test_an_invite_passes_its_name_and_a_candidate_reads_with_theirs(client, companies_api, key):
    body = {"email": "bob@example.com", "name": "Bob Stone"}
    response = call(client, "POST", f"/interviews/{INTERVIEW}/candidates", json=body)

    assert response.status_code == 201
    assert companies_api["names"] == {"bob@example.com": "Bob Stone"}
    assert response.json()["name"] == "Anna Nowak"


def test_an_invite_passes_where_to_return_whether_to_sign_in_and_its_theme(
    client, companies_api, key
):
    body = {
        "email": "bob@example.com",
        "return_url": "https://acme.com/done",
        "sign_in": False,
        "theme": "dark",
    }
    response = call(client, "POST", f"/interviews/{INTERVIEW}/candidates", json=body)

    assert response.status_code == 201
    assert companies_api["options"] == {"bob@example.com": ("https://acme.com/done", False, "dark")}


def test_an_invite_signs_in_and_returns_nowhere_unless_told(client, companies_api, key):
    call(client, "POST", f"/interviews/{INTERVIEW}/candidates", json={"email": "bob@example.com"})

    assert companies_api["options"] == {"bob@example.com": (None, True, None)}


def test_an_invites_default_theme_leaves_it_to_the_candidate(client, companies_api, key):
    body = {"email": "bob@example.com", "theme": "default"}
    call(client, "POST", f"/interviews/{INTERVIEW}/candidates", json=body)

    assert companies_api["options"] == {"bob@example.com": (None, True, None)}


def test_an_invite_with_an_unknown_theme_is_refused(client, companies_api, key):
    body = {"email": "bob@example.com", "theme": "sepia"}

    assert call(client, "POST", f"/interviews/{INTERVIEW}/candidates", json=body).status_code == 422


def test_an_invite_with_a_too_long_name_is_refused(client, companies_api, key):
    body = {"email": "bob@example.com", "name": "x" * 201}

    assert call(client, "POST", f"/interviews/{INTERVIEW}/candidates", json=body).status_code == 422


@pytest.mark.parametrize("refusal", [402, 409, 422, 429, 503])
def test_companies_refusals_pass_through(client, companies_api, key, refusal):
    companies_api["refuse"] = refusal
    response = call(
        client, "POST", f"/interviews/{INTERVIEW}/candidates", json={"email": "bob@example.com"}
    )

    assert response.status_code == refusal


def test_another_companys_interview_is_not_found(client, companies_api, key):
    other = uuid.uuid4()

    assert call(client, "GET", f"/interviews/{other}").status_code == 404
    assert (
        call(
            client, "POST", f"/interviews/{other}/candidates", json={"email": "b@example.com"}
        ).status_code
        == 404
    )
    assert companies_api["sent"] == []


def test_the_public_reference_lists_only_the_public_api(client):
    spec = client.get("/openapi.json").json()

    assert set(spec["paths"]) == {
        "/interviews",
        "/interviews/{interview_id}",
        "/interviews/{interview_id}/candidates",
        "/interviews/{interview_id}/candidates/{candidate_id}",
        "/interviews/{interview_id}/candidates/{candidate_id}/resend",
        "/candidates",
        "/candidates/search",
        "/credits",
    }
    assert list(spec["webhooks"]) == [
        "candidate.finished",
        "candidate.started",
        "candidate.undelivered",
        "candidate.expired",
        "candidate.removed",
        "interview.ready",
        "test",
    ]


def test_the_reference_says_results_must_not_reject_candidates_automatically(client):
    spec = client.get("/openapi.json").json()
    candidate = spec["components"]["schemas"]["Candidate"]["properties"]

    assert "don't reject candidates automatically" in spec["info"]["description"].lower()
    assert "reject a candidate automatically" in candidate["passed"]["description"]
    assert (
        "reject a candidate automatically"
        in spec["components"]["schemas"]["Signals"]["description"]
    )


def test_a_candidate_reads_with_the_flag_extra_time_times_and_sections():
    found = candidate_of(
        candidate(
            flagged=True,
            extra_time=25,
            started_at="2026-10-15T08:00:00Z",
            finished_at="2026-10-15T08:20:00Z",
            sections=[{"title": "SQL", "grade": 90}],
        ),
        COMPANY,
        INTERVIEW,
        "https://prepza.ai",
    )

    assert (found.flagged, found.extra_time) == (True, 25)
    assert found.started_at is not None and found.finished_at is not None
    assert [(section.title, section.grade) for section in found.sections] == [("SQL", 90)]


def test_a_candidate_from_a_list_has_no_sections():
    assert candidate_of(candidate(), COMPANY, INTERVIEW, "https://prepza.ai").sections is None
