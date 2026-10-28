#!/usr/bin/env bash
# Waits for the local stack: runs the smoke test (e2e_tests/smoke.sh: pages and every /ready)
# until it passes, every 15 seconds for up to 10 minutes, which covers the services' start and
# the frontend's first compile. CI's whole-stack job runs it after `docker compose up`.
# Usage: scripts/wait-for-stack.sh
set -euo pipefail

cd "$(dirname "$0")/.."

for _ in $(seq 1 40); do
  if ./e2e_tests/smoke.sh; then
    exit 0
  fi

  sleep 15
done

echo "The stack didn't pass the smoke test in 10 minutes" >&2

exit 1
