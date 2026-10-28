"""The services' layer check (tests/layer_rules.py) finds wrong imports and repositories that
commit, and passes code that keeps the rules."""

from pathlib import Path

import pytest
from layer_rules import layer_problems


def package(root: Path, files: dict[str, str]) -> Path:
    """A service package `svc` with the given modules, plus one repository and one service."""
    base = root / "svc"
    files = {"repositories/rows.py": "", "services/work.py": "", **files}

    for name, code in files.items():
        (base / name).parent.mkdir(parents=True, exist_ok=True)
        (base / name).write_text(code)

    return base


def test_code_that_keeps_the_rules_passes(tmp_path):
    found = package(
        tmp_path,
        {
            "api/v1/routes.py": "from svc.services import work\nfrom svc.repositories import rows\n",
            "handlers/event.py": "from svc.services import work\n",
            "services/work.py": (
                "from svc.core.db import Session\nfrom svc.repositories import rows\n\n"
                "async def run():\n    async with Session.begin() as session:\n"
                "        await rows.add(session)\n"
            ),
            "repositories/rows.py": (
                "from svc.models.base import Base\n\n"
                "async def add(session):\n    await session.flush()\n"
            ),
        },
    )

    assert layer_problems(found) == []


@pytest.mark.parametrize(
    ("path", "code", "problem"),
    [
        ("repositories/rows.py", "from svc.services import work\n", "imports svc.services"),
        ("repositories/rows.py", "from svc import services\n", "imports svc.services"),
        ("repositories/rows.py", "from svc.core.db import Session\n", "imports svc.core.db"),
        ("services/work.py", "from svc.api.v1 import routes\n", "imports svc.api.v1"),
        ("handlers/event.py", "from svc.repositories import rows\n", "imports svc.repositories"),
        ("models/table.py", "import svc.repositories.rows\n", "imports svc.repositories.rows"),
        (
            "repositories/rows.py",
            "async def add(session):\n    await session.commit()\n",
            "calls commit() on line 2",
        ),
        (
            "repositories/rows.py",
            "async def add(factory):\n    async with factory.begin():\n        pass\n",
            "calls begin() on line 2",
        ),
    ],
)
def test_a_broken_rule_is_named(tmp_path, path, code, problem):
    [found] = layer_problems(package(tmp_path, {path: code}))

    assert found == f"{path} {problem}"


def test_a_package_without_repositories_fails_rather_than_passing_on_nothing(tmp_path):
    (tmp_path / "svc" / "services").mkdir(parents=True)
    (tmp_path / "svc" / "services" / "work.py").write_text("")

    with pytest.raises(AssertionError):
        layer_problems(tmp_path / "svc")
