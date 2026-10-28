from langgraph.types import Send

from generation.helpers.questions import topic_size, usable_questions
from generation.models.state import FillTask, State


def fill_topics(state: State) -> dict:
    """Start of the fill: changes nothing; fan_out_fill sends each short topic to its own
    branch, so a retry after one topic failed tops up only that one again."""
    return {}


def fan_out_fill(state: State):
    """Conditional edge: one fill_topic branch per topic below its size; a topic at its size
    needs none, and with none short the run goes straight to join_topics."""
    size = topic_size(state)
    sends = []

    for ti, item in enumerate(state["final"]):
        if len(usable_questions(item)) >= size:
            continue

        task: FillTask = {
            "topic_index": ti,
            "item": item,
            "topic_size": size,
            "multi_share": state["multi_share"],
            "level": state["level"],
            "language": state.get("language"),
        }
        sends.append(Send("fill_topic", task))

    return sends or "join_topics"
