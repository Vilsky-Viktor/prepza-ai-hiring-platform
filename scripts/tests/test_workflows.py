"""What zizmor and actionlint don't check in .github/workflows (.claude/rules/ci.md): every
workflow starts read-only and every job has a timeout."""

import re
from pathlib import Path

WORKFLOWS = sorted((Path(__file__).resolve().parents[2] / ".github" / "workflows").glob("*.yml"))


def jobs(text: str) -> dict[str, str]:
    """Each job's block, by its id."""
    body = text[text.index("\njobs:\n") + len("\njobs:\n") :]
    found = re.split(r"^  ([\w-]+):\n", body, flags=re.MULTILINE)[1:]

    return dict(zip(found[::2], found[1::2], strict=True))


def test_there_are_workflows():
    assert WORKFLOWS


def test_every_workflow_starts_read_only():
    for path in WORKFLOWS:
        assert "\npermissions:\n  contents: read\n" in path.read_text(), path.name


def test_every_job_has_a_timeout():
    for path in WORKFLOWS:
        for name, block in jobs(path.read_text()).items():
            assert re.search(r"^    timeout-minutes: \d+$", block, re.MULTILINE), (
                f"{path.name}: {name}"
            )
