import uuid

from rounds.core.db import Session
from rounds.helpers.scores import invite_grade
from rounds.repositories import sessions


async def scores(invite_ids: list[uuid.UUID]) -> dict[uuid.UUID, dict]:
    """Each candidate's progress, grade, whether they finished, how many answers they picked (not
    timed out: what decides a charge, as in services/sections.py finish), and their integrity
    signals."""
    if not invite_ids:
        return {}

    async with Session() as session:
        counts = await sessions.invite_counts(session, invite_ids)

    return {
        invite_id: {
            **invite_grade(
                found["answered"], found["score_sum"], found["total"], found["finished"]
            ),
            "tab_leaves": found["tab_leaves"],
            "copies": found["copies"],
            "fast_answers": found["fast_answers"],
            "picked": found["picked"],
        }
        for invite_id, found in counts.items()
    }
