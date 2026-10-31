import json
from datetime import UTC, datetime
from pathlib import Path

from testee_common.config.constants import LEGAL_VERSIONS

from site_content.constants.dpa import DPA_INTRO, DPA_SECTIONS
from site_content.constants.privacy import PRIVACY_INTRO, PRIVACY_SECTIONS
from site_content.constants.terms import TERMS_INTRO, TERMS_SECTIONS

# Every version ever published, each a JSON copy at <document>/<version>.json: the current one
# too, so a changed text without a new version is caught (tests/unit/test_legal_versions.py).
# Its translations sit at <document>/<version>/<language>.json; the English is the binding text.
ARCHIVE = Path(__file__).resolve().parents[1] / "legal_versions"

CURRENT = {
    "terms": (TERMS_INTRO, TERMS_SECTIONS),
    "privacy": (PRIVACY_INTRO, PRIVACY_SECTIONS),
    "dpa": (DPA_INTRO, DPA_SECTIONS),
}


def current(document: str) -> dict:
    intro, sections = CURRENT[document]

    return {"intro": intro, "sections": sections}


def versions(document: str) -> list[str]:
    """Its published versions, newest first."""
    return sorted((path.stem for path in (ARCHIVE / document).glob("*.json")), reverse=True)


def in_force(document: str) -> str:
    """The version that applies today (UTC): the newest whose day has come."""
    today = datetime.now(UTC).date().isoformat()
    published = versions(document)

    return next((name for name in published if name <= today), published[-1])


def state(name: str, applies: str) -> str:
    """Whether a version is the one in force (`applies`), one still to come, or one replaced."""
    if name == applies:
        return "in_force"

    return "upcoming" if name > applies else "replaced"


def version(document: str, name: str | None) -> dict | None:
    """The current text, or an earlier version's; None for one never published."""
    if name is None or name == LEGAL_VERSIONS[document]:
        return current(document)

    if name not in versions(document):
        return None

    return json.loads((ARCHIVE / document / f"{name}.json").read_text())


def translation(document: str, name: str, language: str) -> dict | None:
    """A version's text in another language; None when it has no translation (English, or a
    version older than the translations)."""
    path = ARCHIVE / document / name / f"{language}.json"

    if not path.exists():
        return None

    return json.loads(path.read_text())


def archive() -> None:
    """Writes the current versions' copies; an existing copy is never changed."""
    for document, name in LEGAL_VERSIONS.items():
        path = ARCHIVE / document / f"{name}.json"

        if path.exists():
            continue

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(current(document), ensure_ascii=False, indent=2) + "\n")
