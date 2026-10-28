from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from rounds.api.dependencies import ServiceCaller
from rounds.constants.integrity import IntegritySignal
from rounds.core.db import Session
from rounds.helpers.integrity import counted_leave
from rounds.helpers.review import add_signals, build_review
from rounds.helpers.sessions import session_out
from rounds.repositories import answer_counts, sessions
from rounds.schemas.sessions import (
    InviteScoresIn,
    ScorecardSession,
    SessionOut,
    SessionsCreate,
    SetCompaniesIn,
    SetIdsIn,
)
from rounds.services import invite_scores as invite_scores_service
from rounds.services import sections, session_removal
from rounds.services import session_companies as session_companies_service

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
async def create_sessions(body: SessionsCreate, caller: ServiceCaller) -> list[SessionOut]:
    """Creates one session per topic for a candidate invite; returns existing ones if any."""
    return [session_out(row) for row in await sections.start_interview(body)]


@router.post("/session-companies")
async def session_companies(body: SetCompaniesIn, caller: ServiceCaller) -> dict[str, int]:
    """Companies' backfill: the company of each interview set, for the sections started before
    rounds kept it."""
    return {"filled": await session_companies_service.fill(body.companies)}


@router.post("/invite-scores")
async def invite_scores(
    body: InviteScoresIn, caller: ServiceCaller
) -> dict[str, dict[str, int | None]]:
    found = await invite_scores_service.scores(body.invite_ids)

    return {str(invite_id): totals for invite_id, totals in found.items()}


@router.post("/answer-counts")
async def interview_answer_counts(body: SetIdsIn, caller: ServiceCaller) -> dict[str, list[int]]:
    """For the superadmin's pass rates: each interview's answers, [timed out, all]."""
    async with Session() as session:
        found = await answer_counts.for_sets(session, body.set_ids)

    return {str(set_id): counts for set_id, counts in found.items()}


@router.delete("/interviews/{interview_set_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_interview_data(interview_set_id: UUID, caller: ServiceCaller) -> None:
    """Called by companies before it deletes an interview; safe to repeat."""
    await session_removal.remove_interview(interview_set_id)


@router.get("/invites/{invite_id}/scorecard")
async def invite_scorecard(invite_id: UUID, caller: ServiceCaller) -> list[ScorecardSession]:
    async with Session() as session:
        rows = await sessions.list_for_invite(session, invite_id, signals=True)

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
