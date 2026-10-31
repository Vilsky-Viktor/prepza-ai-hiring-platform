from testee_common.ai.examples import example_range, is_formal, pick
from testee_common.ai.multi_answer import multi_count

from generation.helpers.questions import (
    count_examples,
    count_multi,
    merge_buckets,
    normalize,
    reused_questions,
    shifted,
    topic_size,
)
from generation.models.state import State
from generation.services.dedupe import distinct_by_meaning


async def merge_questions(state: State) -> dict:
    """Barrier node: per topic, one list of distinct questions, up to what reuse left to fill: of
    multi-answer ones up to what the topic lacks, and of ones with an example within the
    topic's range (testee_common.ai.examples), less what the reused ones hold."""
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
