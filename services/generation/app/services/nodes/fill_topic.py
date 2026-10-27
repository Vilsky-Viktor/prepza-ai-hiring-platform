from prepza_common.ai.examples import example_range, is_formal
from prepza_common.ai.multi_answer import multi_count

from app.helpers.questions import usable_questions
from app.models.state import FillTask
from app.services.top_up import TopicShortError, top_up


async def fill_topic(task: FillTask) -> dict:
    """Tops up one topic that ended below its size, so it has exactly as many questions, of
    each kind as many as it should (top_up): its share of multi-answer questions and, on
    material in a formal notation, of questions with an example."""
    size = task["topic_size"]
    item = {**task["item"], "questions": list(task["item"]["questions"])}
    usable = usable_questions(item)
    added = len(usable)
    formal = is_formal([question["text"] for question in usable])
    await top_up(
        item,
        usable,
        size,
        multi_count(size, task["multi_share"]),
        example_range(size, formal),
        task,
    )
    item["answer_options"] = list(item["answer_options"]) + [
        question["options"] for question in usable[added:]
    ]

    if len(usable) < size:
        raise TopicShortError(f"Topic {item['topic']!r} has only {len(usable)} questions")

    return {"filled": [{"topic_index": task["topic_index"], "item": item}]}
