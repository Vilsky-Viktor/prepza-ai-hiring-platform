import math

from langgraph.types import Send
from prepza_common.examples import example_count
from prepza_common.multi_answer import multi_count

from app.constants.generation import QUESTION_OVERSAMPLE
from app.helpers.questions import (
    count_examples,
    count_multi,
    question_calls,
    reused_questions,
    split_count,
    topic_size,
)
from app.models.state import QuestionTask, State
from app.services.nodes.questions import focus_for


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
