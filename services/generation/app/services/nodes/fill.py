from prepza_common.examples import example_range, is_formal
from prepza_common.multi_answer import multi_count

from app.helpers.questions import topic_size
from app.models.state import State
from app.services.top_up import TopicShortError, top_up


async def fill_topics(state: State) -> dict:
    """Tops up every topic that ended below its size, so each one has exactly as many questions,
    of each kind as many as it should (top_up): its share of multi-answer questions and, on
    material in a formal notation, of questions with an example."""
    size = topic_size(state)
    final = []

    for item in state["final"]:
        item = {**item, "questions": list(item["questions"])}
        usable = [
            {"text": text, "options": options}
            for text, options in zip(item["questions"], item["answer_options"], strict=True)
            if options
        ]
        added = len(usable)
        formal = is_formal([question["text"] for question in usable])
        await top_up(
            item,
            usable,
            size,
            multi_count(size, state["multi_share"]),
            example_range(size, formal),
            state,
        )
        item["answer_options"] = list(item["answer_options"]) + [
            question["options"] for question in usable[added:]
        ]
        final.append(item)

        if len(usable) < size:
            raise TopicShortError(f"Topic {item['topic']!r} has only {len(usable)} questions")

    return {"final": final}
