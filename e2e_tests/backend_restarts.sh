#!/usr/bin/env bash
# The local backend services run with --reload, so an edit to their code (or packages/common)
# restarts them, mid-run too, and a test that meets the restart fails for a reason of its own.
# The browser scripts call this before a run (--wait: until every service with a health check is
# healthy again) and after it (--since <time>: names each service that restarted during the run,
# so such failures are told apart from real ones).
# Usage: e2e_tests/backend_restarts.sh --wait | --since 2026-10-31T02:00:00Z
set -euo pipefail

cd "$(dirname "$0")/.."

if docker compose version >/dev/null 2>&1; then
  compose=(docker compose)
else
  compose=(docker-compose)
fi

if [[ "${1:-}" == "--wait" ]]; then
  for _ in $(seq 120); do
    if ! "${compose[@]}" ps --format '{{.Service}} {{.Health}}' | grep -qE ' (starting|unhealthy)$'; then
      exit 0
    fi

    sleep 1
  done

  echo "Some backend services aren't healthy after 2 minutes:" >&2
  "${compose[@]}" ps --format '{{.Service}} {{.Health}}' | grep -E ' (starting|unhealthy)$' >&2
  exit 1
fi

restarts="$("${compose[@]}" logs --since "$2" 2>&1 | grep 'Started server process' |
  sed -E 's/^([a-z-]+)-[0-9]+ +\| .*"time": "([^"]+)".*/\1 at \2/' || true)"

if [[ -n "$restarts" ]]; then
  echo "Backend services restarted during this run (an edit to their code); a failure at those times may be the restart's:"
  echo "$restarts"
fi
