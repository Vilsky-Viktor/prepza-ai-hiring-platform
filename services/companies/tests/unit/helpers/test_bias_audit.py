import csv
import io
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

from companies.constants.bias_audit import COLUMNS
from companies.helpers.bias_audit import as_text, audit_csv, medians

INTERVIEW = SimpleNamespace(id=uuid.uuid4(), title="Backend", pass_mark=60)


def invite(grade: int, email: str = "ann@example.com", interview=INTERVIEW):
    return SimpleNamespace(
        id=uuid.uuid4(),
        email=email,
        interview_id=interview.id,
        grade=grade,
        finished_at=datetime(2026, 10, 1, 23, 30, tzinfo=UTC),
    )


def rows_of(text: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(text)))


def test_each_interview_has_its_own_median():
    other = SimpleNamespace(id=uuid.uuid4(), title="Data", pass_mark=50)
    rows = [(invite(grade), INTERVIEW) for grade in (40, 60, 90, 100)] + [
        (invite(10, interview=other), other)
    ]

    assert medians(rows) == {INTERVIEW.id: 75, other.id: 10}


def test_a_row_says_whether_the_candidate_passed_and_scored_above_the_median():
    rows = [(invite(grade, f"{grade}@example.com"), INTERVIEW) for grade in (50, 60, 70)]

    found = rows_of(audit_csv(rows))

    assert [(row["grade"], row["passed"], row["above_median"]) for row in found] == [
        ("50", "false", "false"),
        ("60", "true", "false"),
        ("70", "true", "true"),
    ]
    assert found[0]["finished_on"] == "2026-10-01"
    assert found[0]["candidate_email"] == "50@example.com"
    assert found[0]["interview_title"] == "Backend"


def test_the_export_has_only_outcome_columns():
    """Nothing about who the candidate is beyond the id and the email the company joins its own
    self-reported categories on: no name, no protected characteristic, no proxy."""
    header = next(csv.reader(io.StringIO(audit_csv([]))))

    assert tuple(header) == COLUMNS
    assert {
        "candidate_id",
        "candidate_email",
        "interview_id",
        "interview_title",
        "finished_on",
        "grade",
        "pass_mark",
        "passed",
        "above_median",
    } == set(header)


def test_a_cell_a_spreadsheet_would_run_stays_text():
    assert [as_text(value) for value in ("=SUM(A1)", "+1", "-1", "@x", "Backend", None, 7)] == [
        "'=SUM(A1)",
        "'+1",
        "'-1",
        "'@x",
        "Backend",
        "",
        "7",
    ]
