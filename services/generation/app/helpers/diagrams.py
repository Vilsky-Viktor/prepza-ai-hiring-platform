import re


def graph_mermaid(graph) -> str:
    """A compiled LangGraph graph as Mermaid text, without colors so it reads in dark mode too."""
    return graph.get_graph().draw_mermaid(with_styles=False).strip()


def with_diagram(doc: str, name: str, mermaid: str) -> str:
    """The doc with the Mermaid block between its `<!-- graph:<name> -->` markers replaced."""
    start, end = f"<!-- graph:{name} -->", f"<!-- /graph:{name} -->"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)

    if not pattern.search(doc):
        raise ValueError(f"No {start} … {end} markers in the doc")

    block = f"{start}\n```mermaid\n{mermaid}\n```\n{end}"

    return pattern.sub(lambda _: block, doc, count=1)
