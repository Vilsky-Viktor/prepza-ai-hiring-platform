import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from prepza_common.constants import MAX_UPDATES
from prepza_common.http import bearer
from prepza_common.service_auth import issue_token

from app.helpers.candidate_updates import candidate_updates
from app.helpers.candidates import grade_passed
from app.storage import candidate_updates as updates_storage

SECRET = "test-secret-that-is-at-least-32-bytes"
URL = "/internal/candidates/updates"
SINCE = datetime(2026, 10, 1, 9, tzinfo=UTC)
UNTIL = datetime(2026, 10, 1, 17, tzinfo=UTC)
INTERVIEW = SimpleNamespace(id=uuid.uuid4(), company_id=uuid.uuid4(), title="Backend", pass_mark=70)


def invite(email, started=None, finished=None, undelivered=None, grade=None, name=None):
    return SimpleNamespace(
        id=uuid.uuid4(),
        email=email,
        name=name,
        grade=grade,
        started_at=started,
        finished_at=finished,
        undelivered_at=undelivered,
    )


def at(hours):
    return SINCE + timedelta(hours=hours)


def test_only_steps_after_since_and_up_to_until_count():
    rows = [
        (invite("ann@example.com", started=SINCE), INTERVIEW),
        (invite("bob@example.com", started=UNTIL), INTERVIEW),
        (invite("cid@example.com", undelivered=UNTIL + timedelta(seconds=1)), INTERVIEW),
        (invite("dan@example.com", undelivered=at(1)), INTERVIEW),
    ]

    found = candidate_updates(rows, SINCE, UNTIL)

    assert [(item.email, item.kind) for item in found] == [
        ("bob@example.com", "candidate_started"),
        ("dan@example.com", "invite_undelivered"),
    ]


def test_a_candidate_who_started_and_finished_in_the_window_gives_both_newest_first():
    row = invite("eve@example.com", started=at(1), finished=at(2), grade=80, name="Eve")

    found = candidate_updates([(row, INTERVIEW)], SINCE, UNTIL)

    assert [(item.kind, item.at) for item in found] == [
        ("candidate_finished", at(2)),
        ("candidate_started", at(1)),
    ]
    assert {item.candidate_name for item in found} == {"Eve"}


def test_grade_and_passed_come_only_with_a_finish():
    row = invite("fay@example.com", started=at(1), finished=at(2), grade=80)

    finished, started = candidate_updates([(row, INTERVIEW)], SINCE, UNTIL)

    assert (finished.grade, finished.passed) == (80, True)
    assert (started.grade, started.passed) == (None, None)


def test_passed_follows_the_interview_pass_mark():
    rows = [
        (invite("gil@example.com", finished=at(1), grade=69), INTERVIEW),
        (invite("hal@example.com", finished=at(2), grade=70), INTERVIEW),
        (invite("ida@example.com", finished=at(3)), INTERVIEW),
    ]

    found = candidate_updates(rows, SINCE, UNTIL)

    assert [(item.email, item.grade, item.passed) for item in found] == [
        ("ida@example.com", None, None),
        ("hal@example.com", 70, True),
        ("gil@example.com", 69, False),
    ]


def test_each_update_links_to_the_candidate_page():
    row = invite("jon@example.com", started=at(1))

    (found,) = candidate_updates([(row, INTERVIEW)], SINCE, UNTIL)

    assert found.link == (
        f"/companies/{INTERVIEW.company_id}/interviews/{INTERVIEW.id}/candidates/{row.id}"
    )
    assert (found.company_id, found.interview_id, found.invite_id, found.title) == (
        INTERVIEW.company_id,
        INTERVIEW.id,
        row.id,
        "Backend",
    )


def test_grade_passed_compares_with_the_pass_mark():
    assert grade_passed(70, 70) is True
    assert grade_passed(69, 70) is False
    assert grade_passed(None, 70) is None


def body():
    return {
        "company_ids": [str(INTERVIEW.company_id)],
        "since": SINCE.isoformat(),
        "until": UNTIL.isoformat(),
    }


def test_the_assistant_gets_the_updates(client, monkeypatch):
    asked = []
    row = invite("kim@example.com", finished=at(1), grade=90)

    async def fake_changed(company_ids, since, until, limit):
        asked.append((company_ids, since, until, limit))

        return [(row, INTERVIEW)]

    async def fake_counts(company_ids, since, until):
        return 3, 2, 1, 0

    monkeypatch.setattr(updates_storage, "changed", fake_changed)
    monkeypatch.setattr(updates_storage, "counts", fake_counts)
    token = issue_token("assistant", "companies", SECRET)

    response = client.post(URL, json=body(), headers=bearer(token))

    assert response.status_code == 200
    (item,) = response.json()["items"]
    assert (item["kind"], item["email"], item["grade"], item["passed"]) == (
        "candidate_finished",
        "kim@example.com",
        90,
        True,
    )
    assert item["invite_id"] == str(row.id)
    assert asked == [([INTERVIEW.company_id], SINCE, UNTIL, MAX_UPDATES)]
    # The counts cover every update, not only those listed.
    assert response.json()["counts"] == {
        "candidate_started": 3,
        "candidate_finished": 2,
        "passed": 1,
        "invite_undelivered": 0,
    }


def test_another_service_is_not_allowed(client, monkeypatch):
    async def fake_changed(company_ids, since, until, limit):
        raise AssertionError("not reached")

    monkeypatch.setattr(updates_storage, "changed", fake_changed)
    token = issue_token("ats", "companies", SECRET)

    response = client.post(URL, json=body(), headers=bearer(token))

    assert response.status_code == 403
    assert response.json()["detail"] == "Not allowed"


def test_the_updates_need_a_service_token(client):
    assert client.post(URL, json=body()).status_code == 401
