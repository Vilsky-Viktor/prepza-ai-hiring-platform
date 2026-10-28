"""The layer rules of a service in the src layout (python-services.md, "Routes, services,
repositories"), read from its code: imports go one way (routes and event handlers → services →
repositories → models), handlers reach the database only through services, and repositories
never open a session or commit (the service owning the transaction does). Each moved service's
tests/unit/test_layers.py runs `layer_problems` on its package."""

import ast
from pathlib import Path

# What each layer's modules may not import, by the folder under the service's package.
FORBIDDEN = {
    "models": {"api", "handlers", "services", "repositories"},
    "repositories": {"api", "handlers", "services", "core.db"},
    "services": {"api", "handlers"},
    "handlers": {"api", "repositories"},
}
# Calls that open or end a transaction, which a repository leaves to its caller.
TRANSACTION_CALLS = {"commit", "rollback", "begin", "begin_nested"}


def imports(tree: ast.Module) -> list[list[str]]:
    """Each import statement's modules by their full names, one list a statement (`from x import
    y` names x and x.y, as y may be a module)."""
    found = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found += [[alias.name] for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            found.append([node.module, *(f"{node.module}.{alias.name}" for alias in node.names)])

    return found


def transaction_calls(tree: ast.Module) -> list[str]:
    """The calls in the code that open or end a transaction or a session."""
    found = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        func = node.func

        if isinstance(func, ast.Attribute) and func.attr in TRANSACTION_CALLS:
            found.append(f"{func.attr}() on line {node.lineno}")
        elif isinstance(func, ast.Name) and func.id == "Session":
            found.append(f"Session() on line {node.lineno}")

    return found


def layer_of(module: str, name: str) -> str | None:
    """Which of FORBIDDEN's names a module of package `name` is in (`core.db` for the database
    setup), or None for one outside them or outside the package."""
    parts = module.split(".")

    if parts[0] != name or len(parts) < 2:
        return None

    if parts[1:3] == ["core", "db"]:
        return "core.db"

    return parts[1]


def layer_problems(package: Path) -> list[str]:
    """What breaks the layer rules in the service's package (`src/<service>`), one line each.
    Fails when the package has no repositories or services to check, so a moved folder can't
    make the check pass on nothing."""
    name = package.name
    problems = []

    for layer in ("repositories", "services"):
        assert list((package / layer).glob("*.py")), f"no {layer} in {package}"

    for layer, banned in FORBIDDEN.items():
        for path in sorted((package / layer).rglob("*.py")):
            tree = ast.parse(path.read_text(), str(path))
            where = path.relative_to(package)

            for modules in imports(tree):
                wrong = [module for module in modules if layer_of(module, name) in banned]

                if wrong:
                    problems.append(f"{where} imports {wrong[0]}")

            if layer == "repositories":
                problems += [f"{where} calls {call}" for call in transaction_calls(tree)]

    return problems
