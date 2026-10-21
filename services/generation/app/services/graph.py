from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from app.models.state import State
from app.services.nodes.extraction import extract_info
from app.services.nodes.fill import fill_topics
from app.services.nodes.questions import fan_out_questions, generate_questions, merge_questions
from app.services.nodes.results import collect_results
from app.services.nodes.reuse import find_reused
from app.services.nodes.topics import (
    generate_topics,
    human_review,
    review_router,
    revise_topics,
)


def build_graph(checkpointer: BaseCheckpointSaver):
    """job text -> extraction -> topics -> human review loop -> reused questions ->
    parallel questions with their options -> merge -> final results -> fill short topics."""
    graph = StateGraph(State)
    graph.add_node("extract_info", extract_info)
    graph.add_node("generate_topics", generate_topics)
    graph.add_node("human_review", human_review)
    graph.add_node("revise_topics", revise_topics)
    graph.add_node("find_reused", find_reused)
    graph.add_node("generate_questions", generate_questions)
    graph.add_node("merge_questions", merge_questions)
    graph.add_node("collect_results", collect_results)
    graph.add_node("fill_topics", fill_topics)

    graph.add_edge(START, "extract_info")
    graph.add_edge("extract_info", "generate_topics")
    graph.add_edge("generate_topics", "human_review")
    # Revise loop, or on to reuse.
    graph.add_conditional_edges("human_review", review_router, ["revise_topics", "find_reused"])
    graph.add_edge("revise_topics", "human_review")
    # Stage 1 fan-out.
    graph.add_conditional_edges(
        "find_reused", fan_out_questions, ["generate_questions", "collect_results"]
    )
    # Barrier: merge waits for every question branch.
    graph.add_edge("generate_questions", "merge_questions")
    graph.add_edge("merge_questions", "collect_results")
    graph.add_edge("collect_results", "fill_topics")
    graph.add_edge("fill_topics", END)

    return graph.compile(checkpointer=checkpointer)
