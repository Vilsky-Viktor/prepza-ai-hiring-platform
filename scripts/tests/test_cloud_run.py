"""How Cloud Run runs the services (.claude/rules/python-services.md, FastAPI on Cloud Run): one
uvicorn process per container in exec form, ending in-flight requests within Cloud Run's 10 s
after SIGTERM, and probes that start on /ready and restart only on /health."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SERVICES = sorted(ROOT.glob("services/*/Dockerfile"))


def production_command(dockerfile: Path) -> list[str]:
    """The last CMD (the production stage's), as its exec form's list."""
    found = re.findall(r"^CMD (\[.*?\])$", dockerfile.read_text(), re.MULTILINE | re.DOTALL)

    return json.loads(found[-1].replace("\\\n", ""))


def test_each_service_runs_one_uvicorn_that_stops_within_cloud_runs_grace():
    for dockerfile in SERVICES:
        command = production_command(dockerfile)
        grace = command[command.index("--timeout-graceful-shutdown") + 1]

        assert command[0] == "uvicorn", dockerfile
        assert "--workers" not in command and "--reload" not in command, dockerfile
        assert 5 <= int(grace) <= 8, dockerfile


def test_the_apis_start_on_ready_and_are_restarted_only_on_health():
    services = (ROOT / "infra/terraform/services.tf").read_text()
    startup = re.search(r'dynamic "startup_probe" \{.*?path = "(.*?)"', services, re.DOTALL)
    liveness = re.search(r'dynamic "liveness_probe" \{.*?path = "(.*?)"', services, re.DOTALL)

    assert startup and startup.group(1) == "/ready"
    assert liveness and liveness.group(1) == "/health"
