"""The README names each module of the package in one line (.claude/rules/python-services.md,
Shared library), so a new module is described where people look for it."""

import re
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2]


def test_every_module_has_its_line_in_the_readme():
    listed = set(re.findall(r"^- `(\w+)`: ", (PACKAGE / "README.md").read_text(), re.MULTILINE))
    modules = {
        path.stem
        for path in (PACKAGE / "src/prepza_common").glob("*.py")
        if path.stem != "__init__"
    }

    assert sorted(modules - listed) == []
    assert sorted(listed - modules) == []
