"""The candidate storage the routers use, in memory: a test adds its invites to ROWS."""

from companies.constants.invites import InviteStatus

ROWS = []
# (invite id, grade, flagged) as saved.
SAVED = []


def add(*invites) -> None:
    ROWS.extend(invites)


async def get(interview_id, invite_id):
    return next(
        (row for row in ROWS if row.id == invite_id and row.interview_id == interview_id), None
    )


async def counts(interview_ids):
    found = {}

    for row in ROWS:
        if row.interview_id in interview_ids:
            found[row.interview_id] = found.get(row.interview_id, 0) + 1

    return found


async def any_finished(interview_id):
    return any(
        row.interview_id == interview_id and row.status == InviteStatus.FINISHED for row in ROWS
    )


async def unscored(interview_id):
    return []


async def save_results(results):
    SAVED.extend((invite_id, *result) for invite_id, result in results.items())


async def for_report(interview_id, offset, limit):
    found = [
        row
        for row in ROWS
        if row.interview_id == interview_id and row.status != InviteStatus.DELETED
    ]

    return found[offset : offset + limit]
