import ast
import importlib
from pathlib import Path

from prepza_common.i18n.translations import TRANSLATIONS

from assistant.constants.tool_calls import INVALID_ARGUMENTS

APP = Path(__file__).resolve().parents[2] / "src" / "assistant"
# Names that stay as they are in every language.
NAMES = {"Slack"}


def translated_texts() -> set[str]:
    """Every text the service passes to translate(), read from its code: a constant, or every
    value of a dict of them, looked up where the call is."""
    texts = set()

    for path in APP.rglob("*.py"):
        module = importlib.import_module(
            ".".join(path.relative_to(APP.parent).with_suffix("").parts)
        )

        for node in ast.walk(ast.parse(path.read_text())):
            if not (
                isinstance(node, ast.Call)
                and getattr(node.func, "id", None) == "translate"
                and node.args
            ):
                continue

            first = node.args[0]
            # A dict's lookup, or a constant's .get(): every value the dict holds.
            name = (
                first.value.id
                if isinstance(first, ast.Subscript) and isinstance(first.value, ast.Name)
                else first.func.value.id
                if isinstance(first, ast.Call)
                and isinstance(first.func, ast.Attribute)
                and isinstance(first.func.value, ast.Name)
                else first.id
                if isinstance(first, ast.Name)
                else None
            )
            found = getattr(module, name, None) if name else None

            if isinstance(found, str):
                texts.add(found)
            elif isinstance(found, dict):
                texts |= {value for value in found.values() if isinstance(value, str)}

    return texts


def test_every_text_translate_gets_is_translated():
    texts = translated_texts()

    assert INVALID_ARGUMENTS in texts
    for language, messages in TRANSLATIONS.items():
        missing = sorted(texts - NAMES - set(messages))
        assert missing == [], (language, missing)
