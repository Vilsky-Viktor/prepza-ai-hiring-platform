"""The candidate repository the routes and services use, in memory: a test adds its invites to ROWS."""

from companies.constants.invites import InviteStatus

ROWS = []
# (invite id, grade, flagged) as saved.
SAVED = []


def add(*invites) -> None:
    ROWS.extend(invites)


async def get(session, interview_id, invite_id):
    return next(
        (row for row in ROWS if row.id == invite_id and row.interview_id == interview_id), None
    )


async def counts(session, interview_ids):
    found = {}

    for row in ROWS:
        if row.interview_id in interview_ids:
            found[row.interview_id] = found.get(row.interview_id, 0) + 1

    return found


async def any_finished(session, interview_id):
    return any(
        row.interview_id == interview_id and row.status == InviteStatus.FINISHED for row in ROWS
    )


async def unscored(session, interview_id):
    return []


async def save_results(session, results):
    SAVED.extend((invite_id, *result) for invite_id, result in results.items())


async def for_report(session, interview_id, offset, limit):
    found = [
        row
        for row in ROWS
        if row.interview_id == interview_id and row.status != InviteStatus.DELETED
    ]

    return found[offset : offset + limit]
