import csv
import io
from statistics import median

from companies.constants.bias_audit import COLUMNS, FORMULA_STARTS
from companies.helpers.candidates import grade_passed


def medians(rows: list) -> dict:
    """Each interview's median grade among the rows, the sample a scoring rate is measured
    against (DCWP: the share of a category scoring above the full sample's median)."""
    grades: dict = {}

    for invite, _interview in rows:
        grades.setdefault(invite.interview_id, []).append(invite.grade)

    return {interview_id: median(values) for interview_id, values in grades.items()}


def as_text(value) -> str:
    """A cell as text, a formula-like start kept as text (spreadsheets would run it)."""
    text = "" if value is None else str(value)

    return f"'{text}" if text.startswith(FORMULA_STARTS) else text


def audit_row(invite, interview, middle: float) -> list[str]:
    """One candidate's outcome: who (their id and the email the company joins its own data on),
    the interview, when they finished, their grade, the pass mark, whether they passed it and
    whether they scored above the interview's median."""
    finished = invite.finished_at.date().isoformat() if invite.finished_at else ""
    values = (
        invite.id,
        invite.email,
        interview.id,
        interview.title,
        finished,
        invite.grade,
        interview.pass_mark,
        str(bool(grade_passed(invite.grade, interview.pass_mark))).lower(),
        str(invite.grade > middle).lower(),
    )

    return [as_text(value) for value in values]


def audit_csv(rows: list) -> str:
    """The export's CSV: a header, then a row for each (invite, interview) pair."""
    middles = medians(rows)
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(COLUMNS)

    for invite, interview in rows:
        writer.writerow(audit_row(invite, interview, middles[invite.interview_id]))

    return out.getvalue()
