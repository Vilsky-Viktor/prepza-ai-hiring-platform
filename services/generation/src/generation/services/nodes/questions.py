import logging

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from openai import LengthFinishReasonError

from generation.constants.generation import (
    MAX_OPTION_CHARS,
    OPTIONS,
    QUESTION_ATTEMPTS,
    QUESTION_FOCUSES,
)
from generation.helpers.prompts import bullet_list, language_name
from generation.helpers.questions import build_options, readable, with_example
from generation.integrations import llm
from generation.models.state import QuestionTask
from generation.prompts.questions import QUESTIONS_REQUEST, QUESTIONS_SYSTEM
from generation.schemas.questions import QuestionItemList
from generation.services.key_self_check import keys_that_hold

logger = logging.getLogger(__name__)


def focus_for(call: int, calls: int) -> str:
    if calls == 1:
        return "a mix of " + "; ".join(QUESTION_FOCUSES)

    return QUESTION_FOCUSES[call % len(QUESTION_FOCUSES)]


def question_messages(task: QuestionTask) -> list[BaseMessage]:
    """The instructions, the same for every call so the model's prompt cache keeps them, then
    this call's request."""
    request = QUESTIONS_REQUEST.format(
        level=task["level"],
        topic=task["topic"],
        subtopic=task["subtopic"],
        focus=task.get("focus") or focus_for(0, 1),
        count=task["count"],
        multi=task.get("multi", 0),
        examples=task.get("examples", 0),
        existing=bullet_list(task.get("existing", [])) or "None",
        language=language_name(task.get("language")),
    )

    return [
        SystemMessage(content=QUESTIONS_SYSTEM.format(options=OPTIONS, max_chars=MAX_OPTION_CHARS)),
        HumanMessage(content=request),
    ]


async def generate_questions(task: QuestionTask) -> dict:
    """Questions with their options in one call; ambiguous, too long or incomplete ones are
    dropped."""
    structured_llm = llm.get_generation_llm().with_structured_output(QuestionItemList)
    messages = question_messages(task)
    items = []

    for attempt in range(1, QUESTION_ATTEMPTS + 1):
        try:
            result: QuestionItemList = await structured_llm.ainvoke(messages)
        except LengthFinishReasonError:
            # The model looped until the output cap; ask again.
            logger.warning("Questions for %r ran too long (attempt %d)", task["subtopic"], attempt)

            continue

        items = result.items

        break

    questions = []

    for item in items:
        text = with_example(item.question, item.example, item.example_language)
        usable = not item.ambiguous and readable(item.question, item.example)
        options = build_options(item.correct_options, item.distractors) if usable else None

        if text and options:
            questions.append({"text": text, "options": options})

    questions = await keys_that_hold(questions, task["topic"], task["level"])

    # If every attempt ran too long, this call adds nothing; fill_topics makes up for it.
    return {
        "question_pool": [
            {
                "topic_index": task["topic_index"],
                "subtopic_index": task["subtopic_index"],
                "questions": questions[: task["count"]],
            }
        ]
    }
