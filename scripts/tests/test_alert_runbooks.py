"""Every alert policy in infra/terraform says how bad it is and links its runbook section, every
link points at a section that exists, and every runbook section keeps the four parts
(.claude/rules/operations.md)."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TERRAFORM = ROOT / "infra" / "terraform"
RUNBOOKS = ROOT / "docs" / "runbooks"
PARTS = ("**How you notice", "**What the system does by itself", "**What to do", "**Resolved when")
# The maps whose entries each become an alert policy, with a page flag and a runbook link each.
ALERT_MAPS = ("log_alerts", "slo_alerts")


def terraform() -> str:
    return "\n".join(path.read_text() for path in sorted(TERRAFORM.glob("*.tf")))


def policies() -> dict[str, str]:
    found = re.findall(
        r'^resource "google_monitoring_alert_policy" "(\w+)" \{\n(.*?)^\}',
        terraform(),
        re.MULTILINE | re.DOTALL,
    )

    return dict(found)


def anchor(heading: str) -> str:
    """GitHub's anchor for a heading: lowercase, punctuation dropped, spaces as hyphens."""

    return re.sub(r"[^a-z0-9 -]", "", heading.lower()).replace(" ", "-")


def sections(path: Path) -> dict[str, str]:
    parts = re.split(r"^## ", path.read_text(), flags=re.MULTILINE)[1:]

    return {anchor(part.split("\n", 1)[0]): part for part in parts}


def test_every_alert_policy_sets_its_severity_and_runbook_link():
    found = policies()

    assert found

    for name, body in found.items():
        assert re.search(r"^  severity\s+=", body, re.MULTILINE), name
        assert re.search(r"^    links \{", body, re.MULTILINE), name


def test_every_entry_of_an_alert_map_pages_or_not_and_names_its_runbook():
    text = terraform()

    for name in ALERT_MAPS:
        block = re.search(rf"^  {name} = \{{\n(.*?)^  \}}", text, re.MULTILINE | re.DOTALL)

        assert block, name

        entries = re.findall(
            r"^    (\w+) = \{\n(.*?)^    \}", block.group(1), re.MULTILINE | re.DOTALL
        )

        assert entries, name

        for key, body in entries:
            assert re.search(r"^      page\s+= (true|false)$", body, re.MULTILINE), key
            assert re.search(r'^      runbook\s+= "\w+\.md#[a-z0-9-]+"$', body, re.MULTILINE), key


def test_every_runbook_link_points_at_a_section_that_exists():
    links = re.findall(r'(?:local\.runbooks\}/|runbook\s+= ")(\w+\.md)#([a-z0-9-]+)', terraform())

    assert links

    for page, section in links:
        assert section in sections(RUNBOOKS / page), f"{page}#{section}"


def test_every_runbook_section_keeps_the_four_parts():
    for path in sorted(RUNBOOKS.glob("*.md")):
        for name, body in sections(path).items():
            for part in PARTS:
                assert part in body, f"{path.name}#{name}: {part}"
