import uuid
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from testee_common.limits.limit_list import LIMITS

from rounds.helpers.sessions import new_sections
from rounds.repositories import sessions
from rounds.schemas.library import TopicQuestions
from tests.integration.transactions import transaction

# The signals a question keeps, as the service reads the limit when it isn't edited.
MOST_SIGNALS = LIMITS["MAX_SIGNALS_PER_QUESTION"].default

# A multi-answer question's options: two right of four.
MULTI = [
    {"answer": "right", "correct": True},
    {"answer": "also right", "correct": True},
    {"answer": "wrong", "correct": False},
    {"answer": "also wrong", "correct": False},
]


def topic(size=3, multi=False, texts=None):
    """A topic whose questions all have option "right" as a correct one; multi-answer ones
    (MULTI) with `multi`; questions of the given `texts` instead of `size` short ones."""
    return TopicQuestions.model_validate(
        {
            "id": str(uuid.uuid4()),
            "preparation_id": str(uuid.uuid4()),
            "title": "Python",
            "questions": [
                {
                    "id": str(uuid.uuid4()),
                    "text": text,
                    "options": MULTI
                    if multi
                    else [
                        {"answer": "right", "correct": True},
                        {"answer": "wrong", "correct": False},
                    ],
                }
                for text in texts or [f"Question {index}?" for index in range(size)]
            ],
        }
    )


def option_index(question: dict, correct: bool) -> int:
    return next(i for i, option in enumerate(question["options"]) if option["correct"] == correct)


async def created(
    user_id: str,
    invite_id: uuid.UUID,
    topics: list[TopicQuestions],
    seconds: int | None,
    preview: bool = False,
    practice: bool = False,
    company_id: uuid.UUID | None = None,
):
    """New sections, one a topic, saved as starting an interview or a practice round saves them."""
    rows = new_sections(
        user_id, invite_id, topics, seconds, datetime.now(UTC), preview, practice, company_id
    )
    await transaction(sessions.add_all, rows)

    return rows


async def answered(answer, event: tuple[str, dict] | None = None) -> bool:
    """Saves an answer in a transaction of its own, as the services do: False when its section
    isn't running, or when its question already has one (the unique constraint ends that
    transaction, and nothing of it is kept)."""
    try:
        return await transaction(sessions.add_answer, answer, event)
    except IntegrityError:
        return False
