import logging

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from openai import LengthFinishReasonError

from app.constants.generation import ANSWER_ATTEMPTS, MAX_OPTION_CHARS, OPTIONS
from app.helpers.prompts import language_name
from app.helpers.questions import build_options
from app.integrations import llm
from app.models.state import AnswerTask
from app.prompts.answers import (
    ANSWERS_REQUEST,
    ANSWERS_SYSTEM,
    MULTI_ANSWER_KIND,
    SINGLE_ANSWER_KIND,
)
from app.schemas.questions import AnswerList

logger = logging.getLogger(__name__)


def answers_system(multi: bool) -> SystemMessage:
    return SystemMessage(
        content=ANSWERS_SYSTEM.format(
            options=OPTIONS,
            max_chars=MAX_OPTION_CHARS,
            kind=MULTI_ANSWER_KIND if multi else SINGLE_ANSWER_KIND,
        )
    )


def answers_messages(task: AnswerTask, pending: list[int]) -> list[BaseMessage]:
    """The options call for the questions in `pending` (their indexes in the task)."""
    request = ANSWERS_REQUEST.format(
        level=task["level"],
        topic=task["topic"],
        language=language_name(task.get("language")),
        questions="\n".join(f"[{i}] {task['questions'][i]}" for i in pending),
    )

    return [answers_system(task.get("multi", False)), HumanMessage(content=request)]


def options_of(result: AnswerList, pending: list[int], multi: bool) -> dict[int, list]:
    """Each answered question's options: none for one the model found ambiguous (it's dropped);
    an incomplete or invalid answer is left out, so it can be asked again."""
    done: dict[int, list] = {}

    for item in result.answers:
        if item.id not in pending:
            continue

        if item.ambiguous:
            # More than one defensible answer: drop it (no options) rather than retry.
            done[item.id] = []

            continue

        options = build_options(item.correct_options, item.distractors, multi)

        if options:
            done[item.id] = options

    return done


async def generate_answers(task: AnswerTask) -> dict:
    """Options for questions that already exist: a re-generated question, or new options for one,
    of the kind the task asks for (`multi`: select-all-that-apply)."""
    structured_llm = llm.get_generation_llm().with_structured_output(AnswerList)
    questions = task["questions"]
    multi = task.get("multi", False)
    done: dict = {}
    pending = list(range(len(questions)))

    # Retry only the questions the model skipped or returned incomplete/invalid.
    for _ in range(ANSWER_ATTEMPTS):
        if not pending:
            break

        try:
            result: AnswerList = await structured_llm.ainvoke(answers_messages(task, pending))
        except LengthFinishReasonError:
            # The model looped until the output cap; the next attempt retries the same questions.
            logger.warning("Options for %r ran too long", task["topic"])

            continue

        done |= options_of(result, pending, multi)
        pending = [i for i in pending if i not in done]

    return {
        "answer_pool": [
            {
                "topic_index": task["topic_index"],
                "start": task["start"],
                "options": [done.get(i, []) for i in range(len(questions))],
            }
        ]
    }
