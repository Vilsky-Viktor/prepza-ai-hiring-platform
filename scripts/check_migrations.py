#!/usr/bin/env python3
"""Checks every service's Alembic migrations for the operations `.claude/rules/database.md`
(Migrations without downtime) rules out on a table that already exists, while the old version
serves traffic: an index built without CONCURRENTLY, a foreign key or CHECK added validated
(not NOT VALID), a column's type changed in place, SET NOT NULL without a validated CHECK, and a
rename. A table created in the same migration is new and empty, so anything goes on it.

Migrations older than CHECKED_FROM ran before this check, on empty or small tables, and are
applied everywhere; they're left as they are. A statement the rule allows anyway (a table known
to hold a few rows) carries `# migration-check: <why>` on its line or the line above.

Usage: scripts/check_migrations.py  (exits 1 and lists what it found)"""

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Each service's first migration checked: the next one after those of 2026-10-21.
CHECKED_FROM = {
    "accounts": "0001",
    "api": "0008",
    "assistant": "0011",
    "ats": "0015",
    "billing": "0020",
    "companies": "0053",
    "generation": "0016",
    "library": "0032",
    "notifications": "0013",
    "rounds": "0027",
}
ALLOWED = "# migration-check:"
# Raw SQL: (pattern, what it breaks). Matched on one statement, case-insensitively.
SQL_RULES = [
    (r"\bCREATE\s+(UNIQUE\s+)?INDEX\b(?!\s+CONCURRENTLY)", "an index built without CONCURRENTLY"),
    (
        r"\bADD\s+CONSTRAINT\b(?![^;]*\bNOT\s+VALID\b)(?=[^;]*\b(CHECK|FOREIGN\s+KEY)\b)",
        "a foreign key or CHECK added without NOT VALID",
    ),
    (r"\bALTER\s+COLUMN\s+\w+\s+(SET\s+DATA\s+)?TYPE\b", "a column's type changed in place"),
    (r"\bSET\s+NOT\s+NULL\b", "SET NOT NULL without a validated CHECK (col IS NOT NULL)"),
    (r"\bRENAME\b", "a rename (expand, then contract)"),
]


def keyword(call: ast.Call, name: str):
    """The constant value of a call's keyword argument, or None."""
    for item in call.keywords:
        if item.arg == name:
            return getattr(item.value, "value", True)

    return None


def first_string(call: ast.Call, index: int) -> str | None:
    if len(call.args) > index and isinstance(call.args[index], ast.Constant):
        return call.args[index].value

    return None


def op_calls(tree: ast.Module):
    """Every op.<name>(...) call outside downgrade(), with its name."""
    upgrading = [n for n in tree.body if getattr(n, "name", None) != "downgrade"]

    for node in (inner for part in upgrading for inner in ast.walk(part)):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "op"
        ):
            yield node.func.attr, node


def created_tables(tree: ast.AST) -> set[str]:
    return {first_string(call, 0) for name, call in op_calls(tree) if name == "create_table"}


def sql_text(call: ast.Call) -> str:
    """The SQL an op.execute runs, with f-string parts left as {...}."""
    if not call.args:
        return ""

    node = call.args[0]

    if isinstance(node, ast.Constant):
        return str(node.value)

    if isinstance(node, ast.JoinedStr):
        return "".join(
            str(part.value) if isinstance(part, ast.Constant) else "{...}" for part in node.values
        )

    return ast.unparse(node)


def touches_new_table(sql: str, new: set[str]) -> bool:
    return any(re.search(rf"\b{re.escape(table)}\b", sql) for table in new)


def call_problem(name: str, call: ast.Call, new: set[str]) -> str | None:
    """What an Alembic operation on an existing table breaks, if anything."""
    table_arg = {"create_index": 1, "create_foreign_key": 1, "create_check_constraint": 1}

    if name in table_arg and first_string(call, table_arg[name]) in new:
        return None

    if name == "create_index" and not keyword(call, "postgresql_concurrently"):
        return "an index built without CONCURRENTLY"

    if name in ("create_foreign_key", "create_check_constraint") and not keyword(
        call, "postgresql_not_valid"
    ):
        return "a foreign key or CHECK added without NOT VALID"

    if name == "alter_column" and keyword(call, "type_") is not None:
        return "a column's type changed in place"

    if name == "alter_column" and keyword(call, "nullable") is False:
        return "SET NOT NULL without a validated CHECK (col IS NOT NULL)"

    if name == "alter_column" and keyword(call, "new_column_name"):
        return "a rename (expand, then contract)"

    if name == "rename_table":
        return "a rename (expand, then contract)"

    return None


def problems(source: str) -> list[tuple[int, str]]:
    """What a migration's upgrade breaks: (line, what) for each statement."""
    lines = source.splitlines()
    tree = ast.parse(source)
    new = created_tables(tree)
    found = []

    for name, call in op_calls(tree):
        nearby = lines[max(call.lineno - 2, 0) : call.end_lineno]

        if any(ALLOWED in line for line in nearby):
            continue

        if name == "execute":
            sql = sql_text(call)

            if touches_new_table(sql, new):
                continue

            found += [
                (call.lineno, what)
                for pattern, what in SQL_RULES
                if re.search(pattern, sql, re.IGNORECASE)
                and not (what.startswith("SET NOT NULL") and "IS NOT NULL" in source)
            ]

            continue

        problem = call_problem(name, call, new)

        if problem:
            found.append((call.lineno, problem))

    return found


def main() -> int:
    found = []

    for service, first in sorted(CHECKED_FROM.items()):
        for path in sorted((ROOT / "services" / service / "migrations" / "versions").glob("*.py")):
            if path.name[:4].isdigit() and path.name[:4] >= first:
                found += [
                    f"{path.relative_to(ROOT)}:{line}: {what}"
                    for line, what in problems(path.read_text())
                ]

    for line in found:
        print(line, file=sys.stderr)

    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
