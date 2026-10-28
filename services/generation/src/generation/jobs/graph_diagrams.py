"""Draws the generation graph from the compiled graph itself and writes it into its doc
(docs/generation.md, between the `<!-- graph:generation -->` markers), so the diagram never
drifts from the code. Nothing is sent anywhere: the diagram is Mermaid text, which GitHub draws.

Run from the repo root:
    scripts/graph-diagrams.sh
"""

from langgraph.checkpoint.memory import InMemorySaver

from generation.constants.diagrams import GRAPH_DOC, GRAPH_NAME
from generation.helpers.diagrams import graph_mermaid, with_diagram
from generation.services.graph import build_graph


def write_diagrams() -> None:
    mermaid = graph_mermaid(build_graph(InMemorySaver()))
    doc = GRAPH_DOC.read_text()
    GRAPH_DOC.write_text(with_diagram(doc, GRAPH_NAME, mermaid))


if __name__ == "__main__":
    write_diagrams()
