from prepza_common.db import delete_in_batches
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.constants.rounds import SESSION_DELETE_BATCH
from app.helpers.export import answer_export
from app.models.sessions import Session
from app.storage.db import Session as Db


async def delete_user(user_id: str) -> None:
    """Everything rounds holds about a user: interview and practice sessions with their answers
    and signals, SESSION_DELETE_BATCH sessions at a time, each batch its own transaction. Safe to
    repeat."""
    await delete_in_batches(Db, Session, Session.user_id == user_id, batch=SESSION_DELETE_BATCH)


async def user_ids(practice: bool, after: str, limit: int) -> list[str]:
    """The people who took a company's interview (never a member's own try, a preview), or with
    `practice` a free practice round, once each, in order: up to `limit` after `after`."""
    query = select(Session.user_id).where(Session.user_id > after, Session.practice.is_(practice))

    if not practice:
        query = query.where(Session.preview.is_(False))

    async with Db() as session:
        rows = await session.scalars(query.distinct().order_by(Session.user_id).limit(limit))

        return list(rows)


async def export(user_id: str) -> dict:
    """The user's own data, in plain terms, for their data export."""
    async with Db() as session:
        sessions = await session.scalars(
            select(Session)
            .where(Session.user_id == user_id)
            .options(selectinload(Session.answers), selectinload(Session.signals))
        )

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
                for row in sessions
            ],
        }
