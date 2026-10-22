from app.constants.api import CANDIDATE_LINK, INVITE_LINK
from app.schemas.public import Candidate, Interview, Signals


def interview_of(found: dict) -> Interview:
    """Companies' interview, as the API shows it."""
    return Interview(
        id=found["id"],
        title=found["title"],
        status=found["status"],
        ready=found["set_id"] is not None,
        pass_mark=found["pass_mark"],
        candidate_count=found["candidate_count"],
        created_at=found["created_at"],
        updated_at=found.get("updated_at"),
    )


def candidate_of(found: dict, company_id, interview_id, site: str) -> Candidate:
    """Companies' candidate, as the API shows it, with a link to their results in prepza and,
    until they finish, their invite link."""
    token = found.get("invite_token")

    return Candidate(
        id=found["id"],
        interview_id=interview_id,
        email=found["email"],
        name=found.get("name"),
        status=found["status"],
        progress=found["progress"],
        grade=found["grade"],
        passed=found["passed"],
        signals=Signals(
            tab_leaves=found["tab_leaves"],
            copies=found["copies"],
            fast_answers=found["fast_answers"],
        ),
        flagged=found.get("flagged", False),
        extra_time=found.get("extra_time", 0),
        sections=found.get("sections"),
        results_url=CANDIDATE_LINK.format(
            site=site, company_id=company_id, interview_id=interview_id, invite_id=found["id"]
        ),
        invite_url=INVITE_LINK.format(site=site, token=token) if token else None,
        created_at=found["created_at"],
        updated_at=found.get("updated_at"),
        started_at=found.get("started_at"),
        finished_at=found.get("finished_at"),
    )
