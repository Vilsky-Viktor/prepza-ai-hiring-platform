import uuid
from datetime import UTC, datetime, timedelta

import pytest
from prepza_common.auth.tokens import hashed
from prepza_common.http.http import bearer
from prepza_common.limits import rate_limit
from redis.exceptions import ConnectionError as RedisConnectionError

from app.constants.api import LAST_USED_EVERY
from app.constants.permissions import Permission
from app.helpers.public import candidate_of
from app.integrations import companies
from tests.unit.conftest import CANDIDATE, COMPANY, INTERVIEW, candidate

KEY = "pz_test-key"


@pytest.fixture
def key(stored):
    """A working key of COMPANY, made by u1 (an owner)."""
    row = type("Key", (), {})()
    row.id, row.company_id, row.created_by = uuid.uuid4(), COMPANY, "u1"
    row.hash, row.expires_at, row.last_used_at = hashed(KEY), None, None
    row.permissions = list(Permission)
    stored["keys"].append(row)

    return row


def call(client, method, path, key=KEY, **kwargs):
    headers = bearer(key) if key else {}

    return client.request(method, path, headers=headers, **kwargs)


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

    assert found["signals"] == {"tab_leaves": 0, "copies": 1, "fast_answers": 0}
    assert found["results_url"] == (
        f"http://localhost:8090/companies/{COMPANY}/interviews/{INTERVIEW}/candidates/{CANDIDATE}"
    )
    assert "tab_leaves" not in found
    # Finished: the invite link no longer leads anywhere.
    assert found["invite_url"] is None


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


@pytest.mark.parametrize("sent", [None, "pz_wrong", "not-even-a-key"])
def test_no_key_or_an_unknown_one_is_refused(client, companies_api, stored, sent):
    response = call(client, "GET", "/interviews", key=sent)

    assert response.status_code == 401
    assert stored["used"] == []


def test_an_expired_key_is_refused(client, companies_api, key):
    key.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    response = call(client, "GET", "/interviews")

    assert response.status_code == 401
    assert response.json()["detail"] == "This API key has expired"


@pytest.mark.parametrize("role", ["viewer", None])
def test_a_key_stops_working_once_its_creator_cant_edit(client, companies_api, key, role):
    companies_api["roles"]["u1"] = role

    assert call(client, "GET", "/interviews").status_code == 401


def test_over_the_rate_limit_is_refused(client, companies_api, key, stored):
    stored["limited"] = True

    assert call(client, "GET", "/interviews").status_code == 429


def test_a_companys_keys_share_one_rate_limit(client, companies_api, key, stored):
    other = type("Key", (), {})()
    other.id, other.company_id, other.created_by = uuid.uuid4(), COMPANY, "u1"
    other.hash, other.expires_at, other.last_used_at = hashed("pz_other"), None, None
    other.permissions = list(Permission)
    stored["keys"].append(other)
    call(client, "GET", "/interviews")
    call(client, "GET", "/interviews", key="pz_other")

    assert stored["counted"] == [f"rate:api:{COMPANY}"] * 2


def test_a_key_whose_creator_lost_access_isnt_counted(client, companies_api, key, stored):
    companies_api["roles"]["u1"] = "viewer"

    assert call(client, "GET", "/interviews").status_code == 401
    assert stored["counted"] == []


def test_with_redis_down_requests_go_through_unlimited(client, companies_api, key, monkeypatch):
    async def down(*args, **kwargs):
        raise RedisConnectionError("down")

    monkeypatch.setattr(rate_limit, "hit", down)

    assert call(client, "GET", "/interviews").status_code == 200


def test_companies_is_asked_about_the_keys_maker_once_a_minute(
    client, companies_api, key, monkeypatch
):
    asked = []
    access = companies.access

    async def counted(company_id, user_id):
        asked.append(user_id)

        return await access(company_id, user_id)

    monkeypatch.setattr(companies, "access", counted)
    call(client, "GET", "/interviews")
    call(client, "GET", "/interviews")

    assert asked == ["u1"]


def test_a_key_used_within_the_minute_isnt_noted_again(client, companies_api, key, stored):
    key.last_used_at = datetime.now(UTC) - timedelta(seconds=10)
    call(client, "GET", "/interviews")
    key.last_used_at = datetime.now(UTC) - LAST_USED_EVERY
    call(client, "GET", "/interviews")

    assert stored["used"] == [key.id]


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
