"""Generation's work for a waiting caller ends before the caller gives up, and the caller's wait
ends before its own request does (.claude/rules/scalability.md, Timeouts)."""

import re
from pathlib import Path

from prepza_common.config.constants import HTTP_TIMEOUT_SECONDS, PUBLISH_IN_REQUEST_TIMEOUT_SECONDS

from app.constants.generation import ENQUEUE_TIMEOUT_SECONDS, REGENERATE_TIMEOUT_SECONDS

ROOT = Path(__file__).resolve().parents[4]


def constant(path: str, name: str) -> int:
    return int(re.search(rf"^{name} = (\d+)$", (ROOT / path).read_text(), re.MULTILINE).group(1))


def cloud_run_timeout(service: str) -> int:
    services = (ROOT / "infra/terraform/locals.tf").read_text()

    return int(
        re.search(rf"^\s+{service}\s+= {{.*?timeout = (\d+)", services, re.MULTILINE).group(1)
    )


def test_a_regeneration_ends_before_companies_stops_waiting_for_it():
    waits = constant("services/companies/app/constants/generation.py", "REGENERATE_CALL_SECONDS")
    # Reading the question and saving the new one, and recording two models' usage.
    work = (
        REGENERATE_TIMEOUT_SECONDS
        + 2 * HTTP_TIMEOUT_SECONDS
        + 2 * PUBLISH_IN_REQUEST_TIMEOUT_SECONDS
    )

    assert work < waits < cloud_run_timeout("companies")
    assert waits < cloud_run_timeout("generation")


def test_queueing_a_job_ends_well_before_companies_stops_waiting():
    assert ENQUEUE_TIMEOUT_SECONDS * 2 < HTTP_TIMEOUT_SECONDS
