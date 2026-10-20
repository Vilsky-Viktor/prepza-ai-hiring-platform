import logging
import math

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.types import Send
from openai import LengthFinishReasonError
from prepza_common.examples import example_count, example_range, is_formal, pick
from prepza_common.multi_answer import multi_count

from app.constants.generation import (
    MAX_OPTION_CHARS,
    OPTIONS,
    QUESTION_ATTEMPTS,
    QUESTION_FOCUSES,
    QUESTION_OVERSAMPLE,
)
from app.helpers.prompts import bullet_list, language_name
from app.helpers.questions import (
    build_options,
    count_examples,
    count_multi,
    merge_buckets,
    normalize,
    question_calls,
    readable,
    shifted,
    split_count,
    topic_size,
    with_example,
)
from app.integrations import llm
from app.models.state import QuestionTask, State
from app.prompts.questions import QUESTIONS_REQUEST, QUESTIONS_SYSTEM
from app.schemas.questions import QuestionItemList
from app.services.dedupe import distinct_by_meaning
from app.services.key_self_check import keys_that_hold

logger = logging.getLogger(__name__)


def reused_questions(state: State, topic_index: int) -> list[dict]:
    reused = state.get("reused") or []

    return reused[topic_index] if reused else []


def focus_for(call: int, calls: int) -> str:
    if calls == 1:
        return "a mix of " + "; ".join(QUESTION_FOCUSES)

    return QUESTION_FOCUSES[call % len(QUESTION_FOCUSES)]


def fan_out_questions(state: State):
    """Conditional edge: one branch per call of each (topic, subtopic), for what reuse left; the
    multi-answer questions the topic still lacks, and the examples it would have on material in
    a formal notation, are spread over its calls."""
    sends = []

    for ti, topic in enumerate(state["topics"]):
        subtopics = topic["subtopics"] or [topic["main_topic"]]
        reused = reused_questions(state, ti)
        size = topic_size(state)
        missing = max(size - len(reused), 0)
        multi = min(missing, max(multi_count(size, state["multi_share"]) - count_multi(reused), 0))
        examples = min(missing, max(example_count(size) - count_examples(reused), 0))
        per_subtopic = math.ceil(missing * QUESTION_OVERSAMPLE / len(subtopics))
        calls = question_calls(len(subtopics), size)
        counts = [count for _ in subtopics for count in split_count(per_subtopic, calls)]
        multis = split_count(multi, len(counts))
        shown = split_count(examples, len(counts))
        bucket = 0

        for subtopic in subtopics:
            for call in range(calls):
                task: QuestionTask = {
                    "topic_index": ti,
                    "topic": topic["main_topic"],
                    "subtopic_index": bucket,
                    "subtopic": subtopic,
                    "count": counts[bucket],
                    "multi": min(multis[bucket], counts[bucket]),
                    "examples": min(shown[bucket], counts[bucket]),
                    "level": state["level"],
                    "existing": [question["text"] for question in reused],
                    "focus": focus_for(call, calls),
                    "language": state.get("language"),
                }
                sends.append(Send("generate_questions", task))
                bucket += 1

    return sends or "collect_results"


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


async def merge_questions(state: State) -> dict:
    """Barrier node: per topic, one list of distinct questions, up to what reuse left to fill: of
    multi-answer ones up to what the topic lacks, and of ones with an example within the
    topic's range (prepza_common.examples), less what the reused ones hold."""
    topic_questions: list[list[dict]] = []

    for ti in range(len(state["topics"])):
        entries = [entry for entry in state.get("question_pool", []) if entry["topic_index"] == ti]
        entries.sort(key=lambda entry: entry["subtopic_index"])
        reused = reused_questions(state, ti)
        taken = {normalize(question["text"]) for question in reused}
        merged = [
            question
            for question in merge_buckets([entry["questions"] for entry in entries])
            if normalize(question["text"]) not in taken
        ]
        texts = [question["text"] for question in reused + merged]
        kept = await distinct_by_meaning(texts, keep_first=len(reused))
        distinct = [merged[index - len(reused)] for index in kept if index >= len(reused)]
        size = topic_size(state)
        missing = max(size - len(reused), 0)
        multi = min(missing, max(multi_count(size, state["multi_share"]) - count_multi(reused), 0))
        formal = is_formal([question["text"] for question in reused + distinct])
        examples = shifted(example_range(size, formal), count_examples(reused))
        topic_questions.append(pick(distinct, missing, multi, examples)[0])

    return {"topic_questions": topic_questions}
