from pathlib import Path

# The generation graph's diagram lives in the generation doc, between its markers.
GRAPH_NAME = "generation"
GRAPH_DOC = Path(__file__).resolve().parents[4] / "docs" / "generation.md"
GRAPH_SCRIPT = "scripts/graph-diagrams.sh"
