from rounds.core.db import Session
from rounds.helpers.export import answer_export
from rounds.repositories import accounts


async def remove_user(user_id: str) -> None:
    """Everything rounds holds about a user, a batch of sessions at a time; safe to repeat."""
    await accounts.delete_user(Session, user_id)


async def export_user(user_id: str) -> dict:
    """The user's own data, in plain terms, for their data export."""
    async with Session() as session:
        rows = await accounts.of_user(session, user_id)

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
    }
