from datetime import datetime

from app.constants.notifications import CANDIDATE_LINK
from app.helpers.candidates import grade_passed
from app.models.interviews import Interview
from app.models.invites import CandidateInvite
from app.schemas.candidate_updates import CandidateUpdateOut

STARTED = "candidate_started"
FINISHED = "candidate_finished"
UNDELIVERED = "invite_undelivered"


def candidate_updates(
    rows: list[tuple[CandidateInvite, Interview]], since: datetime, until: datetime
) -> list[CandidateUpdateOut]:
    """Each step a candidate took after `since` and up to `until` (one who started and finished
    meanwhile has both), newest first."""
    found = []

    for invite, interview in rows:
        steps = {
            STARTED: invite.started_at,
            FINISHED: invite.finished_at,
            UNDELIVERED: invite.undelivered_at,
        }
        link = CANDIDATE_LINK.format(
            company_id=interview.company_id, interview_id=interview.id, invite_id=invite.id
        )

        for kind, at in steps.items():
            if at is None or not since < at <= until:
                continue

            finished = kind == FINISHED
            found.append(
                CandidateUpdateOut(
                    kind=kind,
                    at=at,
                    company_id=interview.company_id,
                    interview_id=interview.id,
                    title=interview.title,
                    invite_id=invite.id,
                    email=invite.email,
                    candidate_name=invite.name,
                    grade=invite.grade if finished else None,
                    passed=grade_passed(invite.grade, interview.pass_mark) if finished else None,
                    link=link,
                )
            )

    return sorted(found, key=lambda item: item.at, reverse=True)


def update_counts(started: int, finished: int, passed: int, undelivered: int) -> dict[str, int]:
    """Every step's count by kind, and how many of the finished passed."""
    return {STARTED: started, FINISHED: finished, "passed": passed, UNDELIVERED: undelivered}
