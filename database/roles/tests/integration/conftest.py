"""Integration tests need the local stack's Postgres. They run only with INTEGRATION_TESTS set
(see scripts/integration.sh); plain `pytest` skips them."""

import os

if not os.getenv("INTEGRATION_TESTS"):
    collect_ignore_glob = ["test_*.py"]
