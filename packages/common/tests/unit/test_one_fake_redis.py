"""Test fakes of shared clients live once beside this package's tests and are imported by the
services, never copied (.claude/rules/python-services.md, Redis; CLAUDE.md rule 10)."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SHARED = ROOT / "packages/common/tests/fake_redis.py"
# A class of Redis of a test's own; one that only builds on the shared fake (a Redis that fails
# at a chosen step) isn't a copy.
COPY = re.compile(r"^class \w*Redis\w*\b(?!\((FakeRedis|DownRedis)\))", re.MULTILINE)


def test_no_service_keeps_a_fake_redis_of_its_own():
    tests = list(ROOT.glob("services/*/tests/**/*.py")) + list(
        ROOT.glob("packages/common/tests/**/*.py")
    )
    copies = [
        str(path.relative_to(ROOT))
        for path in tests
        if path != SHARED and COPY.search(path.read_text())
    ]

    assert SHARED.exists()
    assert copies == []
