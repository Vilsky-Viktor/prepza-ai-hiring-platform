"""The AI rules a computer can check (.claude/rules/ai.md and evals.md), over the whole repo,
without running any service: every prompt's system message starts with a role, no prompt
shouts or asks a reasoning model to think step by step, every model call sends a system
message, structured output is a Pydantic schema with a description on every field, every AI
action has an eval, and every judge has a role."""

import ast
import re
from pathlib import Path

from service_code import service_code

ROOT = Path(__file__).resolve().parents[2]
PROMPTS = service_code(ROOT, "prompts/*.py")
APP = service_code(ROOT)
# System messages without a role, on purpose: the MCP server's instructions go to an AI app
# whose own system prompt sets the role.
NO_ROLE = {"MCP_INSTRUCTIONS"}
# Words in capitals that shout an instruction (acronyms like JSON or ATS are fine).
SHOUTED = {"ALWAYS", "NEVER", "MUST", "IMPORTANT", "CRITICAL", "EVERY", "ALL", "ONE", "EACH"}
SHOUTED |= {"ONLY", "NOT", "YES", "NO", "DO", "DON'T"}
# Modules that send messages to a model with the system message made elsewhere: the retry of a
# topic draft adds to the conversation the draft started.
SYSTEM_ELSEWHERE = {"services/generation/app/services/topic_planning.py"}
# Helpers that send a schema as structured output (the Batch API's request bodies): the
# position of the schema among their arguments, and its parameter's name there.
SCHEMA_HELPERS = {"request_body": 3, "translation_body": 1, "writing_body": 1}
SCHEMA_PARAMETER = "schema"


def constants(path: Path) -> dict[str, ast.expr]:
    tree = ast.parse(path.read_text())

    return {
        target.id: node.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }


ALL_CONSTANTS = {name: value for path in PROMPTS for name, value in constants(path).items()}


def opening(value: ast.expr) -> str:
    """The text a prompt constant starts with: its first literal, following concatenations,
    f-strings and other prompt constants by name."""
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return value.value

    if isinstance(value, ast.BinOp):
        return opening(value.left)

    if isinstance(value, ast.JoinedStr) and value.values:
        first = value.values[0]

        return opening(first.value if isinstance(first, ast.FormattedValue) else first)

    if isinstance(value, ast.Name) and value.id in ALL_CONSTANTS:
        return opening(ALL_CONSTANTS[value.id])

    return ""


def test_every_system_prompt_starts_with_a_role():
    systems = [n for n in ALL_CONSTANTS if n.endswith(("_SYSTEM", "_ROLE")) or n in NO_ROLE]
    missing = [
        name
        for name in systems
        if name not in NO_ROLE
        and not opening(ALL_CONSTANTS[name]).lstrip("\\\n").startswith("You are")
    ]

    assert len(systems) >= 15
    assert missing == []


def test_no_prompt_shouts_or_asks_to_think_step_by_step():
    found = []

    for path in PROMPTS:
        text = path.read_text()

        for word in re.findall(r"\b[A-Z][A-Z']{1,}\b", text):
            if word in SHOUTED:
                found.append(f"{path.relative_to(ROOT)}: {word}")

        if re.search(r"step by step|step-by-step", text, re.IGNORECASE):
            found.append(f"{path.relative_to(ROOT)}: step by step")

    assert found == []


def test_every_model_call_sends_a_system_message():
    """A module that writes a user's message to a model writes its system message too."""
    missing = [
        str(path.relative_to(ROOT))
        for path in APP
        if "HumanMessage(" in (text := path.read_text())
        and "SystemMessage(" not in text
        and str(path.relative_to(ROOT)) not in SYSTEM_ELSEWHERE
    ]

    assert missing == []


def structured_schemas() -> set[str]:
    """The classes the services send as structured output: to with_structured_output, or in
    a Batch API request."""
    found = set()

    for path in APP:
        for node in ast.walk(ast.parse(path.read_text())):
            if (
                isinstance(node, ast.Call)
                and getattr(node.func, "attr", None) == "with_structured_output"
                and node.args
            ):
                assert isinstance(node.args[0], ast.Name), f"{path}: a schema, not a dict"
                assert not {k.arg for k in node.keywords} & {"method"}, f"{path}: default method"
                found.add(node.args[0].id)

            # A schema handed to a helper that sends it as structured output.
            found |= helper_schema(node)

    return found - {SCHEMA_PARAMETER}


def helper_schema(node: ast.AST) -> set[str]:
    func = getattr(node, "func", None)
    name = getattr(func, "id", None) or getattr(func, "attr", None)
    position = SCHEMA_HELPERS.get(name)

    if position is None or len(node.args) <= position:
        return set()

    schema = node.args[position]

    return {schema.id} if isinstance(schema, ast.Name) else set()


def test_structured_output_is_a_schema_with_a_description_on_every_field():
    schemas = structured_schemas()
    classes = {
        node.name: node
        for path in service_code(ROOT, "schemas/*.py")
        for node in ast.parse(path.read_text()).body
        if isinstance(node, ast.ClassDef)
    }
    undescribed = []

    # A schema's nested models need descriptions too.
    for name in list(schemas):
        for node in ast.walk(classes[name]):
            if isinstance(node, ast.Name) and node.id in classes:
                schemas.add(node.id)

    for name in schemas:
        for field in classes[name].body:
            if not isinstance(field, ast.AnnAssign):
                continue

            described = (
                isinstance(field.value, ast.Call)
                and getattr(field.value.func, "id", None) == "Field"
                and any(k.arg == "description" for k in field.value.keywords)
            )

            if not described:
                undescribed.append(f"{name}.{field.target.id}")

    assert len(schemas) >= 10
    assert undescribed == []


def test_every_ai_action_has_an_eval():
    source = (ROOT / "packages/common/src/prepza_common/ai/ai_constants.py").read_text()
    actions = constants_dict(source, "ACTIONS")
    readme = (ROOT / "evals/README.md").read_text()
    table = readme[readme.index("## Every AI action and its eval") :]
    missing = [action for action in actions if f"`{action}`" not in table]
    scripts = set(re.findall(r"`(\w+\.py)`", table))
    absent = [s for s in scripts if not (ROOT / "evals/scripts" / s).exists()]

    assert len(actions) >= 15
    assert (missing, absent) == ([], [])


def constants_dict(source: str, name: str) -> list[str]:
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", None) == name:
            return [key.value for key in node.value.keys]

    raise AssertionError(name)


def test_every_judge_has_a_role():
    judges = sorted((ROOT / "evals/judges").glob("*.md"))
    missing = [path.name for path in judges if not path.read_text().startswith("You are")]

    assert len(judges) >= 10
    assert missing == []
