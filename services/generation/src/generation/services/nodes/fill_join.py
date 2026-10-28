from generation.models.state import State


def join_topics(state: State) -> dict:
    """Barrier node: every topic in its order, the filled ones from their fill_topic branch."""
    filled = {entry["topic_index"]: entry["item"] for entry in state.get("filled", [])}

    return {"final": [filled.get(ti, item) for ti, item in enumerate(state["final"])]}
