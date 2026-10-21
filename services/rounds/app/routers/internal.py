from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.constants.integrity import IntegritySignal
from app.helpers.integrity import counted_leave
from app.helpers.review import add_signals, build_review
from app.helpers.sessions import session_out
from app.schemas.sessions import (
    InviteScoresIn,
    ScorecardSession,
    SessionOut,
    SessionsCreate,
    SetIdsIn,
)
from app.service_auth import ServiceCaller
from app.storage import answer_counts, sessions

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
async def create_sessions(body: SessionsCreate, caller: ServiceCaller) -> list[SessionOut]:
    """Creates one session per topic for a candidate invite; returns existing ones if any."""
    existing = await sessions.list_for_invite(body.candidate_invite_id)

    if existing:
        return [session_out(row) for row in existing]

    try:
        rows = await sessions.create_many(
            body.user_id,
            body.candidate_invite_id,
            body.topics,
            body.question_seconds,
            body.preview,
            company_id=body.company_id,
        )
    except IntegrityError:
        # Another start for the same invite got there first: theirs are the sections.
        rows = await sessions.list_for_invite(body.candidate_invite_id)

    return [session_out(row) for row in rows]


@router.post("/invite-scores")
async def invite_scores(
    body: InviteScoresIn, caller: ServiceCaller
) -> dict[str, dict[str, int | None]]:
    found = await sessions.scores_for_invites(body.invite_ids)

    return {str(invite_id): totals for invite_id, totals in found.items()}


@router.post("/answer-counts")
async def interview_answer_counts(body: SetIdsIn, caller: ServiceCaller) -> dict[str, list[int]]:
    """For the superadmin's pass rates: each interview's answers, [timed out, all]."""
    found = await answer_counts.for_sets(body.set_ids)

    return {str(set_id): counts for set_id, counts in found.items()}


@router.delete("/interviews/{interview_set_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_interview_data(interview_set_id: UUID, caller: ServiceCaller) -> None:
    """Called by companies before it deletes an interview; safe to repeat."""
    await sessions.remove_for_interview(interview_set_id)


@router.get("/invites/{invite_id}/scorecard")
async def invite_scorecard(invite_id: UUID, caller: ServiceCaller) -> list[ScorecardSession]:
    rows = await sessions.list_for_invite(invite_id, signals=True)

    if not rows:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No sessions for this invite")

    cards = []

    for row in rows:
        review = build_review(row)
        add_signals(review, row.signals)
        kinds = [signal.kind for signal in row.signals]
        cards.append(
            ScorecardSession(
                id=row.id,
                topic_title=row.topic_title,
                status=row.status,
                final_score=row.final_score,
                tab_leaves=sum(counted_leave(signal) for signal in row.signals),
                copies=kinds.count(IntegritySignal.COPY),
                fast_answers=sum(item.answer is not None and item.answer.fast for item in review),
                review=review,
            )
        )

    return cards
