"""Every way a service's server starts (its images, Cloud Run's worker, the local worker) leaves
out uvicorn's `server` header, which tells anyone what runs behind the site."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
START = re.compile(r'"uvicorn",[^\]]*\]', re.DOTALL)


def test_every_uvicorn_start_leaves_out_the_server_header():
    files = list(ROOT.glob("services/*/Dockerfile"))
    files += [ROOT / "infra/terraform/locals.tf", ROOT / "compose/services.yml"]
    starts = [(path.name, found) for path in files for found in START.findall(path.read_text())]

    # Two per image (development and production), and the worker's in Cloud Run and locally.
    assert len(starts) >= 2 * len(list(ROOT.glob("services/*/Dockerfile"))) + 2
    assert [name for name, found in starts if "--no-server-header" not in found] == []
