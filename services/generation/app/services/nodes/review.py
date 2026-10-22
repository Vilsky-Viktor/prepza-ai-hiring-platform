from langgraph.types import interrupt

from app.models.state import State


def human_review(state: State) -> dict:
    # Pauses the graph until the API resumes it with {"selected": [topic indices to keep],
    # "instructions": "free text or empty", "topics": [every topic, edited by hand] or null}.
    response = interrupt({"topics": state["topics"]}) or {}
    keep = set(response.get("selected") or [])
    edited = response.get("topics")
    # Edits made by hand need no model call; an edited list must match the drafted one.
    topics = edited if edited and len(edited) == len(state["topics"]) else state["topics"]
    kept = [topic for index, topic in enumerate(topics) if index in keep]
    instructions = (response.get("instructions") or "").strip()

    # Empty instructions mean approved; otherwise the topics go to revise_topics.
    return {"topics": kept, "feedback": instructions, "approved": not instructions}


def review_router(state: State):
    """Conditional edge after human_review: revise again, or look for questions to reuse."""
    if not state.get("approved"):
        return "revise_topics"

    return "find_reused"
