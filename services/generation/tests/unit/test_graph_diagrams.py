import pytest
from langgraph.checkpoint.memory import InMemorySaver

from app.constants.diagrams import GRAPH_DOC, GRAPH_NAME, GRAPH_SCRIPT
from app.helpers.diagrams import graph_mermaid, with_diagram
from app.services.graph import build_graph

DOC = "Intro\n\n<!-- graph:demo -->\nold\n<!-- /graph:demo -->\n\nAfter\n"


def test_doc_diagram_matches_the_graph():
    doc = GRAPH_DOC.read_text()
    mermaid = graph_mermaid(build_graph(InMemorySaver()))

    assert with_diagram(doc, GRAPH_NAME, mermaid) == doc, (
        f"{GRAPH_DOC.name}'s diagram differs from the graph: run {GRAPH_SCRIPT}"
    )


def test_diagram_has_every_step_and_the_review_loop():
    mermaid = graph_mermaid(build_graph(InMemorySaver()))

    assert "human_review -.-> revise_topics;" in mermaid
    assert "revise_topics --> human_review;" in mermaid
    assert "find_reused -.-> generate_questions;" in mermaid
    assert "fill_topics --> __end__;" in mermaid
    assert "classDef" not in mermaid


def test_with_diagram_replaces_only_the_block_between_its_markers():
    doc = with_diagram(DOC, "demo", "graph TD;\n\ta --> b;")

    assert doc == (
        "Intro\n\n<!-- graph:demo -->\n```mermaid\ngraph TD;\n\ta --> b;\n```\n"
        "<!-- /graph:demo -->\n\nAfter\n"
    )
    assert with_diagram(doc, "demo", "graph TD;\n\ta --> b;") == doc


def test_with_diagram_refuses_a_doc_without_markers():
    with pytest.raises(ValueError, match="graph:demo"):
        with_diagram("No markers", "demo", "graph TD;")
