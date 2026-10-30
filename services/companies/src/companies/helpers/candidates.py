import uuid

from companies.constants.invites import NOT_STARTED, OPEN, SIGNAL_KEYS, InviteStatus
from companies.schemas.invites import CandidateOut, CompanyCandidateOut


def new_hold_key(interview_id) -> str:
    """A new invite's own key for its credits, without the candidate's email (billing keeps its
    keys as long as the company): a candidate invited again after their invite was removed gets
    a new one, so they're charged again (billing keeps a charged key charged)."""
    return f"{interview_id}:{uuid.uuid4().hex}"


def candidate_label(invite) -> str:
    """How a message names the candidate: "Name (email)", or the email while the name is
    unknown."""
    return f"{invite.name} ({invite.email})" if invite.name else invite.email


def passed(totals: dict, pass_mark: int) -> bool | None:
    """Whether a finished candidate reached the pass mark; None before they finish."""
    if not totals.get("finished") or totals.get("grade") is None:
        return None

    return grade_passed(totals["grade"], pass_mark)


def grade_passed(grade: int | None, pass_mark: int) -> bool | None:
    """Whether a grade reaches the pass mark; None without a grade."""
    if grade is None:
        return None

    return grade >= pass_mark


def finished_result(interview, invite_id, grade: int | None, flagged: bool) -> dict:
    """The candidate.finished event: what ats writes back to the ATS that sent the candidate, in
    the interview's language."""
    return {
        "candidate_invite_id": str(invite_id),
        "interview_id": str(interview.id),
        "company_id": str(interview.company_id),
        "title": interview.title or "",
        "language": interview.language,
        "grade": grade,
        "passed": bool(grade_passed(grade, interview.pass_mark)),
        "flagged": flagged,
    }


def section_passed(section: dict, pass_mark: int) -> bool | None:
    """Whether a finished section's score reached the pass mark; None while it's still going."""
    if section.get("status") != "finished" or section.get("final_score") is None:
        return None

    return section["final_score"] >= pass_mark


def flagged(totals: dict) -> bool:
    """True when the candidate has any integrity signal."""
    return any(totals.get(key) for key in SIGNAL_KEYS)


def stored_results(totals: dict) -> tuple[int | None, bool]:
    """What the invite keeps of a finished candidate's results: their grade and integrity flag."""
    return totals.get("grade"), flagged(totals)


def open_link_token(invite) -> str | None:
    """The invite link's token while it still leads somewhere: until the candidate finishes, and
    not once the invite expired (sending it again revives it)."""
    return invite.token if invite.status in OPEN else None


def candidate_out(invite, totals: dict, interview, with_link: bool = False) -> CandidateOut:
    """A candidate row: the invite, with their results from rounds; `with_link` adds the invite
    link's token (the public API)."""
    return CandidateOut(
        id=invite.id,
        email=invite.email,
        name=invite.name,
        status=invite.status,
        progress=totals.get("progress", 0),
        grade=totals.get("grade"),
        passed=passed(totals, interview.pass_mark),
        **{key: totals.get(key, 0) for key in SIGNAL_KEYS},
        flagged=bool(invite.flagged),
        extra_time=invite.extra_time or 0,
        voice=takes_voice(invite, interview),
        created_at=invite.created_at,
        updated_at=invite.updated_at,
        started_at=invite.started_at,
        finished_at=invite.finished_at,
        invite_token=open_link_token(invite) if with_link else None,
        **row_actions(invite.status),
    )


def company_candidate_out(
    invite, totals: dict, interview, with_link: bool = False
) -> CompanyCandidateOut:
    """A candidate row of the company's search: the candidate row, with its interview."""
    return CompanyCandidateOut(
        **candidate_out(invite, totals, interview, with_link).model_dump(),
        interview_id=interview.id,
        interview_title=interview.title,
    )


def candidate_seconds(question_seconds: int, extra_time: int | None) -> int:
    """A candidate's average time a question, with any extra time they were given: rounds fits
    each question's own time to it, so every question gets the same share more and the total
    stays exact in whole seconds."""
    return round(question_seconds * (100 + (extra_time or 0)) / 100)


def row_actions(status: str) -> dict:
    """What a candidate's row offers, by their invite's status."""
    return {
        "can_resend": status not in (InviteStatus.FINISHED, InviteStatus.DELETED),
        "revokable": status in NOT_STARTED,
    }


def unstarted(invite) -> bool:
    """Whether what's fixed at the start (extra time, the mode) can still change: not started,
    and no start making their sessions."""
    return invite.status in NOT_STARTED and invite.starting_at is None


def takes_voice(invite, interview) -> bool:
    """Whether the candidate takes the interview by voice: their own mode when the company set
    one, else the interview's."""
    return bool(interview.voice) if invite.voice is None else invite.voice


def voice_override(voice: bool, interview) -> bool | None:
    """What a candidate's chosen mode keeps on their invite: None when it's the interview's own,
    so they follow the interview's when it changes; the choice when it's apart from it."""
    return None if voice == bool(interview.voice) else voice
