import json
from pathlib import Path

from testee_common.ai.page_keys import PAGE_KEYS
from testee_common.config.constants import DEFAULT_LANGUAGE, LANGUAGES

# Each page's guide (what it's for, what you can do there, tips) in every language, one file per
# language at <language>.json, by the page's key (testee_common's PAGE_KEYS).
GUIDES_FOLDER = Path(__file__).resolve().parents[1] / "page_guides"

GUIDES = {
    code: json.loads((GUIDES_FOLDER / f"{code}.json").read_text(encoding="utf-8"))
    for code in LANGUAGES
}


def page_guide(key: str, language: str) -> dict | None:
    """A page's guide in `language`, in English until it's translated; None for an unknown key."""
    if key not in PAGE_KEYS:
        return None

    return GUIDES[language].get(key) or GUIDES[DEFAULT_LANGUAGE].get(key)


def guide_text(guide: dict) -> str:
    """A guide as plain text, for a model to read."""
    lines = [guide["title"], guide["text"], "What you can do here:"]
    lines += [f"- {item}" for item in guide["actions"]]
    lines.append("Tips:")
    lines += [f"- {item}" for item in guide["tips"]]

    return "\n".join(lines)
