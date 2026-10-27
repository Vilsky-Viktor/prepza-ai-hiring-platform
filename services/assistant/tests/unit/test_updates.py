"""get_updates' result: where each update comes from, the summary, the grouping and the cap."""

from datetime import UTC, datetime, timedelta

from prepza_common.config.constants import MAX_UPDATES

from app.helpers.updates import (
    counts_of,
    credits_low,
    events_of,
    grouped,
    parsed_since,
    summary,
    updates_result,
)

ACME = "8c1d2b8e-1a2b-4c3d-8e9f-0a1b2c3d4e5f"
GLOBEX = "00000000-0000-4000-8000-000000000099"
NAMES = {ACME: "Acme", GLOBEX: "Globex"}
SITE = "https://prepza.example"
START = datetime(2026, 10, 1, 9, tzinfo=UTC)


def at(minutes: int) -> str:
    return (START + timedelta(minutes=minutes)).isoformat()


def candidate(kind: str, minutes: int, company=ACME, title="Backend", **more) -> dict:
    return {
        "kind": kind,
        "at": at(minutes),
        "company_id": company,
        "interview_id": "i1",
        "title": title,
        "invite_id": "v1",
        "email": f"{kind}@example.com",
        "candidate_name": "Ann",
        "link": f"/companies/{company}/candidates/{minutes}",
        **more,
    }


def bell(kind: str, minutes: int, company=ACME, **data) -> dict:
    return {
        "id": "n1",
        "kind": kind,
        "link": f"/companies/{company}/bell/{minutes}",
        "data": data,
        "created_at": at(minutes),
        "company_id": company,
    }


def test_a_time_without_a_zone_is_utc_and_anything_else_is_none():
    assert parsed_since("2026-10-01T09:00:00") == START
    assert parsed_since("2026-10-01T11:00:00+02:00") == START
    assert parsed_since("yesterday") is None


def test_the_bell_never_tells_what_a_service_tells_one_by_one():
    candidates = [candidate("candidate_finished", 3, grade=80, passed=True)]
    not_invited = [{**candidate("x", 2), "ats": "Greenhouse", "reason": "no_email"}]
    questions = [
        {
            "kind": "question_flagged",
            "at": at(1),
            "company_id": ACME,
            "title": "Backend",
            "topic": "SQL",
            "link": "/q",
        }
    ]
    bells = [
        bell("candidate_finished", 4, title="Backend", count=2),
        bell("candidate_started", 4),
        bell("invite_undelivered", 4),
        bell("ats_not_invited", 4),
        bell("question_flagged", 4),
        bell("question_fixed", 4),
        bell("interview_ready", 5, title="Frontend"),
        bell("auto_top_up", 0, credits=2500),
    ]

    events = events_of(candidates, not_invited, questions, bells)

    assert [(event["kind"], event["at"]) for event in events] == [
        ("interview_ready", at(5)),
        ("candidate_finished", at(3)),
        ("ats_not_invited", at(2)),
        ("question_flagged", at(1)),
        ("auto_top_up", at(0)),
    ]
    assert events[1] == {
        "kind": "candidate_finished",
        "at": at(3),
        "company_id": ACME,
        "title": "Backend",
        "email": "candidate_finished@example.com",
        "candidate_name": "Ann",
        "grade": 80,
        "passed": True,
        "link": f"/companies/{ACME}/candidates/3",
    }
    assert events[2]["ats"] == "Greenhouse" and events[2]["reason"] == "no_email"
    assert events[3]["topic"] == "SQL"
    assert events[4]["credits"] == 2500


def test_the_summary_counts_each_kind_the_passed_and_the_companies_low_on_credits():
    """The services count their own updates (they list only the newest); the bell's other
    notifications are counted from the list."""
    candidates = {
        "items": [],
        "counts": {
            "candidate_started": 1,
            "candidate_finished": 2,
            "passed": 1,
            "invite_undelivered": 1,
        },
    }
    questions = {"items": [], "counts": {"question_flagged": 3, "question_fixed": 0}}
    events = events_of([], [], [], [bell("auto_top_up", 0), bell("auto_top_up", 1)])
    counts = counts_of(candidates, {"items": [], "total": 4}, questions, events)
    low = [credits_low({"company_id": GLOBEX, "candidates": 0})]

    assert summary(counts, low) == {
        "candidate_started": 1,
        "candidate_finished": 2,
        "passed": 1,
        "invite_undelivered": 1,
        "ats_not_invited": 4,
        "question_flagged": 3,
        "auto_top_up": 2,
        "credits_low": 1,
    }


def test_updates_are_grouped_by_company_then_interview_with_links_on_the_site():
    events = events_of(
        [
            candidate("candidate_finished", 3, grade=80, passed=True),
            candidate("candidate_started", 2, company=GLOBEX, title="Sales"),
            candidate("candidate_started", 1),
        ],
        [],
        [],
        [bell("auto_top_up", 0, credits=2500)],
    )

    companies = grouped(events, NAMES, SITE)

    assert [(company["name"], len(company["interviews"])) for company in companies] == [
        ("Acme", 1),
        ("Globex", 1),
    ]
    backend = companies[0]["interviews"][0]
    assert backend["title"] == "Backend"
    assert [update["kind"] for update in backend["updates"]] == [
        "candidate_finished",
        "candidate_started",
    ]
    assert backend["updates"][0]["link"] == f"{SITE}/companies/{ACME}/candidates/3"
    assert "company_id" not in backend["updates"][0]
    assert companies[0]["other"] == [
        {
            "kind": "auto_top_up",
            "at": at(0),
            "credits": 2500,
            "link": f"{SITE}/companies/{ACME}/bell/0",
        }
    ]


def test_at_most_the_cap_is_listed_but_the_summary_counts_them_all():
    events = events_of(
        [candidate("candidate_started", minutes) for minutes in range(MAX_UPDATES)], [], [], []
    )
    low = [credits_low({"company_id": ACME, "candidates": 0})]
    # Companies listed its newest MAX_UPDATES and counted every one.
    counts = {"candidate_started": MAX_UPDATES + 10, "passed": 0}

    result = updates_result(events, counts, low, NAMES, START, SITE)
    acme = result["companies"][0]
    listed = acme["interviews"][0]["updates"]

    assert result["since"] == START.isoformat()
    assert result["summary"] == {"candidate_started": MAX_UPDATES + 10, "credits_low": 1}
    assert (result["shown"], result["more"]) == (MAX_UPDATES, True)
    assert len(listed) == MAX_UPDATES
    assert listed[0]["at"] == at(MAX_UPDATES - 1)
    assert acme["other"] == [
        {"kind": "credits_low", "candidates_left": 0, "link": f"{SITE}/top-up"}
    ]


def test_under_the_cap_nothing_says_there_are_more():
    result = updates_result([], {}, [], {}, START, SITE)

    assert result == {"since": START.isoformat(), "summary": {}, "companies": []}
