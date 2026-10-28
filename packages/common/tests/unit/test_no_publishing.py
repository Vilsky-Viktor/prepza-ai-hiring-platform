"""No test publishes to Pub/Sub (tests/no_publishing.py): every service's tests take the shared
fixtures, none keeps a fake of its own, and a test whose code reaches Pub/Sub anyway fails."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SHARED = ROOT / "packages/common/tests/no_publishing.py"
IMPORT = "from no_publishing import no_publishing, published"
# Generation is moving to the src layout in its own change; it takes the fixtures with it.
MOVING = {"generation"}
COPY = re.compile(r"^\s*(async )?def publish_batch\(", re.MULTILINE)

pytest_plugins = ["pytester"]


def services():
    return sorted(
        path.parent.name
        for path in ROOT.glob("services/*/pyproject.toml")
        if path.parent.name not in MOVING
    )


def test_every_service_takes_the_shared_fixtures_in_all_its_tests():
    missing = [
        name
        for name in services()
        if IMPORT not in (ROOT / "services" / name / "tests/conftest.py").read_text()
    ]

    assert len(services()) >= 8
    assert missing == []


def test_no_service_keeps_a_fake_publisher_of_its_own():
    tests = [
        path for name in services() for path in (ROOT / "services" / name / "tests").rglob("*.py")
    ]
    copies = [str(path.relative_to(ROOT)) for path in tests if COPY.search(path.read_text())]

    assert copies == []


def test_events_published_in_a_test_are_kept_for_it_to_read(pytester):
    pytester.makepyfile(
        f"""
        import asyncio

        {IMPORT}  # noqa: F401
        from prepza_common.events import pubsub


        def test_publishes(published):
            asyncio.run(pubsub.publish("candidate.invited", {{"invite_id": "i-1"}}))

            assert published == [("candidate.invited", {{"invite_id": "i-1"}})]
        """
    )

    pytester.runpytest_inprocess("-p", "no:randomly").assert_outcomes(passed=1)


def test_a_test_that_reaches_pub_sub_past_the_fixture_fails(pytester):
    pytester.makepyfile(
        f"""
        import httpx

        {IMPORT}  # noqa: F401

        URL = "http://localhost:8085/v1/projects/demo-test/topics/events:publish"


        def test_publishes_by_hand():
            try:
                httpx.post(URL, json={{"messages": []}})
            except RuntimeError:
                pass
        """
    )

    result = pytester.runpytest_inprocess("-p", "no:randomly")

    result.assert_outcomes(passed=1, errors=1)
    result.stdout.fnmatch_lines(["*The test published to Pub/Sub*events:publish*"])
