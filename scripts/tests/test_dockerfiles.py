"""The services', the database users job's and the frontend's images (.claude/rules/ci.md): base images pinned by tag and
digest, packages only from the lock, no build tools (uv) in the production stage, and a non-root
user there."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# The services' and the database users job's Python images.
SERVICES = [*sorted(ROOT.glob("services/*/Dockerfile")), ROOT / "database" / "roles" / "Dockerfile"]
DOCKERFILES = [*SERVICES, ROOT / "frontend" / "Dockerfile"]


def stages(text: str) -> dict[str, str]:
    """Each stage's lines after its FROM, by the stage's name, without comments."""
    text = re.sub(r"^#.*\n", "", text, flags=re.MULTILINE)
    parts = re.split(r"^FROM (\S+)(?: AS (\w+))?\n", text, flags=re.MULTILINE)[1:]

    return {name: body for _, name, body in zip(parts[::3], parts[1::3], parts[2::3], strict=True)}


def test_there_are_dockerfiles():
    assert len(SERVICES) > 1


def test_outside_images_are_pinned_by_tag_and_digest():
    for path in DOCKERFILES:
        text = path.read_text()
        names = set(re.findall(r"^FROM \S+ AS (\w+)$", text, re.MULTILINE))
        images = re.findall(r"^FROM (\S+)", text, re.MULTILINE)
        images += re.findall(r"COPY --from=(\S+:\S+)", text)

        for image in images:
            if image not in names:
                assert re.fullmatch(r"[\w./-]+:[\w.-]+@sha256:[0-9a-f]{64}", image), (path, image)


def test_packages_install_only_from_the_lock():
    for path in SERVICES:
        installs = re.findall(r"uv sync[^\n]*", path.read_text())

        assert installs, path
        assert all("--locked" in line for line in installs), path

    assert "pnpm install --frozen-lockfile" in (ROOT / "frontend" / "Dockerfile").read_text()


def test_the_production_stage_has_no_uv_and_runs_as_another_user():
    for path in DOCKERFILES:
        text = path.read_text()
        prod = stages(text)["prod"]
        base = re.search(r"^FROM (\S+) AS prod$", text, re.MULTILINE).group(1)

        assert "uv" not in re.findall(r"\b\w+\b", prod), path
        assert "uv" not in re.findall(r"\b\w+\b", stages(text).get(base, "")), path
        assert re.search(r"^USER (?!root)\w+", prod, re.MULTILINE), path
