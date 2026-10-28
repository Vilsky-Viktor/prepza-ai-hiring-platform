from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from generation.models.state import State
from generation.services.nodes.extraction import extract_info
from generation.services.nodes.fan_out import fan_out_questions
from generation.services.nodes.fill import fan_out_fill, fill_topics
from generation.services.nodes.fill_join import join_topics
from generation.services.nodes.fill_topic import fill_topic
from generation.services.nodes.merge import merge_questions
from generation.services.nodes.questions import generate_questions
from generation.services.nodes.results import collect_results
from generation.services.nodes.reuse import find_reused
from generation.services.nodes.review import human_review, review_router
from generation.services.nodes.revision import revise_topics
from generation.services.nodes.topics import generate_topics


def build_graph(checkpointer: BaseCheckpointSaver):
    """job text -> extraction -> topics -> human review loop -> reused questions ->
    parallel questions with their options -> merge -> final results -> parallel fill of short
    topics -> join."""
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
    graph.add_node("fill_topic", fill_topic)
    graph.add_node("join_topics", join_topics)

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
    # Stage 2 fan-out: one branch per short topic, so a retry re-runs only the failed ones.
    graph.add_conditional_edges("fill_topics", fan_out_fill, ["fill_topic", "join_topics"])
    graph.add_edge("fill_topic", "join_topics")
    graph.add_edge("join_topics", END)

    return graph.compile(checkpointer=checkpointer)
