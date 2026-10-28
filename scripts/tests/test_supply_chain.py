"""Supply chain (.claude/rules/ci.md): every lock file is kept current by Dependabot, and the
images scripts run outside compose are pinned by digest as the Dockerfiles' are."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCKS = {
    "package-lock.json": "npm",
    "pnpm-lock.yaml": "npm",
    "uv.lock": "uv",
    ".terraform.lock.hcl": "terraform",
}
SKIPPED = ("node_modules", ".venv", ".terraform/")


def covered() -> set[tuple[str, str]]:
    """(ecosystem, directory) for each directory dependabot.yml lists."""
    text = (ROOT / ".github" / "dependabot.yml").read_text()
    found = set()

    for block in re.split(r"\n  - package-ecosystem: ", text)[1:]:
        ecosystem = block.split("\n", 1)[0].strip()
        directories = re.findall(r"^\s+(?:directory: |- )(/\S*)$", block, re.MULTILINE)
        found |= {(ecosystem, directory) for directory in directories}

    return found


def test_every_lock_file_is_updated_by_dependabot():
    listed = covered()

    for name, ecosystem in LOCKS.items():
        for lock in ROOT.rglob(name):
            path = lock.relative_to(ROOT).as_posix()

            if any(part in path for part in SKIPPED):
                continue

            directory = "/" + lock.parent.relative_to(ROOT).as_posix()
            assert (ecosystem, directory) in listed, path


def test_images_scripts_run_are_pinned_by_digest():
    scripts = [*ROOT.glob("scripts/*.sh"), *ROOT.glob("e2e_tests/*.sh")]
    images = [
        (path.name, image)
        for path in scripts
        for image in re.findall(r"\b(mcr\.microsoft\.com/\S+|docker\.io/\S+)", path.read_text())
    ]

    assert images
    for name, image in images:
        assert re.fullmatch(r"[\w./-]+:[\w.-]+@sha256:[0-9a-f]{64}", image), (name, image)
