"""No log call passes an email, a name, a token, a key or a secret (the privacy and security
rules): every logger call in the services and the shared library is read, and any argument
whose variable is named so fails here. Log ids, counts and outcomes instead."""

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
LEVELS = {"debug", "info", "warning", "error", "exception", "critical", "log"}
# The last part of a variable's name that says it holds what logs must never carry.
PERSONAL = re.compile(
    r"(^|_)(email|emails|address|name|token|secret|password|key|api_key|authorization|cookie"
    r"|body|content|text|message|comment|url|webhook)$",
    re.IGNORECASE,
)
# Names that end so but hold none of it: a kind's or a route's name, a limit's name, an event's
# type, a hashed or keyed value, a logger's own message template.
SAFE = {"name", "event_type", "kind", "action", "limit", "route", "key_id", "hook_id"}


# Arguments named so that hold none of it, by file and name, with why.
ALLOWED = {
    # The keyed hash of an address (helpers/unsubscribe.py address_hash), never the address.
    "services/notifications/app/services/suppression.py address",
    "services/notifications/app/services/admin_opt_outs.py address",
    # The local job's internal address (a route of ours), only when running without Google.
    "services/generation/app/integrations/tasks.py url",
    # A limit's name, as limit_list.LIMITS names it.
    "packages/common/src/prepza_common/limits.py key",
}


def names(node) -> list[str]:
    """What an argument is called when it's passed as is: `x` or `a.x`. A call or an expression
    made of it (an id list, a kind) is the code's choice of what to log."""
    if isinstance(node, ast.Name):
        return [node.id]

    if isinstance(node, ast.Attribute):
        return [node.attr]

    return []


def offending(path: Path) -> list[str]:
    tree = ast.parse(path.read_text())
    found = []

    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in LEVELS
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in {"logger", "logging", "log"}
        ):
            continue

        for argument in node.args[1:]:
            for name in names(argument):
                where = f"{path.relative_to(ROOT)} {name}"

                if PERSONAL.search(name) and name not in SAFE and where not in ALLOWED:
                    found.append(f"{path.relative_to(ROOT)}:{node.lineno} {name}")

    return found


def test_no_log_call_passes_personal_data_or_a_secret():
    files = list(ROOT.glob("services/*/app/**/*.py"))
    files += list(ROOT.glob("packages/common/src/prepza_common/**/*.py"))
    found = [line for path in files for line in offending(path)]

    assert len(files) > 300
    assert found == []


def test_a_log_call_passing_an_email_or_token_is_caught(tmp_path, monkeypatch):
    monkeypatch.setitem(globals(), "ROOT", tmp_path)
    code = tmp_path / "x.py"
    code.write_text(
        'logger.info("Invited %s", user.email)\n'
        'logger.warning("Bad %s", token)\n'
        'logger.info("Invite %s for %s", invite.id, kind_of(email))\n'
    )

    assert offending(code) == ["x.py:1 email", "x.py:2 token"]
