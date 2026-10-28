"""Every Redis key that isn't a deliberate switch has a TTL, set in the same command or the same
transaction (.claude/rules/scalability.md, Redis): a write without one is allowed only where its
function also sets the key's expiry, or listed here with why."""

import ast
from pathlib import Path

from service_code import service_code

ROOT = Path(__file__).resolve().parents[4]
WRITES = {"set", "hset", "sadd", "lpush", "rpush", "zadd", "incr", "incrby", "hincrby", "setex"}
EXPIRIES = {"ex", "px", "exat", "pxat", "keepttl"}

# Keys kept without an expiry on purpose, by file and the key's name.
ALLOWED = {
    # The switches: on until a superadmin turns them off.
    "packages/common/src/prepza_common/limits/pause.py PAUSE_KEY",
    "packages/common/src/prepza_common/limits/maintenance.py MAINTENANCE_KEY",
    "packages/common/src/prepza_common/limits/maintenance.py MAINTENANCE_STARTED_KEY",
    # The limits edited in Controls, rewritten from Postgres every 5 minutes.
    "services/billing/src/billing/services/limit_values.py LIMITS_KEY",
}


def expires(function: ast.AST) -> bool:
    """Whether the function sets an expiry: an expire call, or a write with one."""
    for node in ast.walk(function):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in {"expire", "pexpire", "expireat"}:
                return True

            if {keyword.arg for keyword in node.keywords} & EXPIRIES:
                return True

    return False


def unexpired(path: Path) -> list[str]:
    found = []
    tree = ast.parse(path.read_text())
    where = str(path.relative_to(ROOT))

    for function in ast.walk(tree):
        if not isinstance(function, ast.FunctionDef | ast.AsyncFunctionDef):
            continue

        for node in ast.walk(function):
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in WRITES
                and node.args
            ):
                continue

            # A context variable's or a set's one-argument `set` isn't Redis's.
            if node.func.attr == "set" and len(node.args) < 2:
                continue

            key = ast.unparse(node.args[0])

            if expires(function) or f"{where} {key}" in ALLOWED:
                continue

            found.append(f"{where}:{node.lineno} {key}")

    return found


def test_every_redis_key_expires_unless_it_is_a_switch():
    files = service_code(ROOT)
    files += list(ROOT.glob("packages/common/src/prepza_common/**/*.py"))
    found = [line for path in files for line in unexpired(path)]

    assert len(files) > 300
    assert found == []


def test_a_key_written_without_an_expiry_is_caught(tmp_path, monkeypatch):
    monkeypatch.setitem(globals(), "ROOT", tmp_path)
    code = tmp_path / "x.py"
    code.write_text(
        "async def keep(redis):\n"
        "    await redis.set(KEY, 1)\n"
        "\n"
        "async def counted(redis):\n"
        "    async with redis.pipeline() as pipe:\n"
        "        pipe.incr(COUNT)\n"
        "        pipe.expire(COUNT, 60)\n"
    )

    assert unexpired(code) == ["x.py:2 KEY"]
