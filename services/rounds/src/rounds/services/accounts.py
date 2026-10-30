from rounds.core.db import Session
from rounds.helpers.export import answer_export
from rounds.repositories import accounts, open_to_offers


async def remove_user(user_id: str) -> None:
    """Everything rounds holds about a user: their Open to offers opt-in and its consent log
    first (off every Discover tab at once), then their sessions, a batch at a time; safe to
    repeat."""
    async with Session.begin() as session:
        await open_to_offers.delete_user(session, user_id)

    await accounts.delete_user(Session, user_id)


async def export_user(user_id: str) -> dict:
    """The user's own data, in plain terms, for their data export."""
    async with Session() as session:
        rows = await accounts.of_user(session, user_id)
        offers = await open_to_offers.get(session, user_id)
        consents = await open_to_offers.consents(session, user_id)

    return {
        "interview_sections": [
            {
                "topic": row.topic_title,
                "status": row.status,
                # Their own grade, in practice and in a company's interview alike; which
                # answers were right only for practice (answer_export).
                "final_score": row.final_score,
                "started_at": row.started_at,
                "answers": [
                    {**answer_export(row.questions, a, row.practice), "seconds": a.seconds}
                    for a in row.answers
                ],
                "page_leaves_and_copies": [
                    {"kind": s.kind, "question_id": s.question_id, "at": s.created_at}
                    for s in row.signals
                ],
            }
            for row in rows
        ],
        # Shared with paying companies' Discover tabs while on, with their practice results.
        "open_to_offers": (
            {
                "name": offers.name,
                "linkedin_url": offers.linkedin_url,
                "turned_on_at": offers.opened_at,
            }
            if offers
            else None
        ),
        "open_to_offers_changes": [
            {"on": c.granted, "wording_version": c.text_version, "at": c.created_at}
            for c in consents
        ],
    }
