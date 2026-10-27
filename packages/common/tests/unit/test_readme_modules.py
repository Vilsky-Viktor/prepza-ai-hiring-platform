"""The README names each module of the package in one line, under its area's folder
(.claude/rules/python-services.md, Shared library), so a new module is described where people
look for it."""

import re
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2]


def test_every_module_has_its_line_under_its_area_in_the_readme():
    readme = (PACKAGE / "README.md").read_text().split("## Modules", 1)[1]
    listed = {
        (area, module)
        for area, section in re.findall(
            r"^### `(\w+)/`\n(.*?)(?=^### |\Z)", readme, re.MULTILINE | re.DOTALL
        )
        for module in re.findall(r"^- `(\w+)`: ", section, re.MULTILINE)
    }
    modules = {
        (path.parent.name, path.stem)
        for path in (PACKAGE / "src/prepza_common").glob("*/*.py")
        if path.stem != "__init__"
    }

    assert len(modules) > 50
    assert sorted(modules - listed) == []
    assert sorted(listed - modules) == []
