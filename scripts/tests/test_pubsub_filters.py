"""Each consumer's Pub/Sub filter, built as infra/terraform/pubsub.tf builds it, stays within the
256 bytes Pub/Sub allows."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIMIT = 256


def filters() -> dict[str, str]:
    block = re.search(
        r"consumes = \{(.*?)\n  \}", (ROOT / "infra/terraform/pubsub.tf").read_text(), re.DOTALL
    )
    found = {}

    for name, types in re.findall(r"^\s+(\w+)\s*=\s*\[(.*?)\]", block.group(1), re.MULTILINE):
        clauses = [
            f'attributes.family = "{kind[:-2]}"'
            if kind.endswith(".*")
            else f'attributes.type = "{kind}"'
            for kind in re.findall(r'"([^"]+)"', types)
        ]
        found[name] = " OR ".join(clauses)

    return found


def test_every_consumers_filter_fits_pubsubs_limit():
    built = filters()

    assert {"notifications", "ats", "companies", "api"} <= set(built)
    assert {name: len(text) for name, text in built.items() if len(text.encode()) > LIMIT} == {}
