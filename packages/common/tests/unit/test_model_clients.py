"""Every model client the services build has a timeout and its retries stated (.claude/rules/
ai.md: models built with a timeout and max_retries from constants), so no call waits on a
library's default."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CLIENTS = {"chat_model", "ChatOpenAI", "AsyncOpenAI", "OpenAI", "OpenAIEmbeddings"}


def clients(path: Path) -> list[tuple[str, set]]:
    """The model clients built in a file: where, and the arguments they're given."""
    built = []

    for node in ast.walk(ast.parse(path.read_text())):
        if not isinstance(node, ast.Call):
            continue

        name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
        given = {keyword.arg for keyword in node.keywords}

        if name in CLIENTS:
            built.append((f"{path.relative_to(ROOT)}:{node.lineno} {name}", given))

    return built


def test_every_model_client_states_its_timeout_and_retries():
    built = [client for path in ROOT.glob("services/*/app/**/*.py") for client in clients(path)]
    unbounded = [where for where, given in built if not {"timeout", "max_retries"} <= given]

    assert len(built) >= 5
    assert unbounded == []
