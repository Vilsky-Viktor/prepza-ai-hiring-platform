import uuid

from rounds.schemas.library import TopicQuestions

# A multi-answer question's options: two right of four.
MULTI = [
    {"answer": "right", "correct": True},
    {"answer": "also right", "correct": True},
    {"answer": "wrong", "correct": False},
    {"answer": "also wrong", "correct": False},
]


def topic(size=3, multi=False):
    """A topic whose questions all have option "right" as a correct one; multi-answer ones
    (MULTI) with `multi`."""
    return TopicQuestions.model_validate(
        {
            "id": str(uuid.uuid4()),
            "preparation_id": str(uuid.uuid4()),
            "title": "Python",
            "questions": [
                {
                    "id": str(uuid.uuid4()),
                    "text": f"Question {index}?",
                    "options": MULTI
                    if multi
                    else [
                        {"answer": "right", "correct": True},
                        {"answer": "wrong", "correct": False},
                    ],
                }
                for index in range(size)
            ],
        }
    )


def option_index(question: dict, correct: bool) -> int:
    return next(i for i, option in enumerate(question["options"]) if option["correct"] == correct)
