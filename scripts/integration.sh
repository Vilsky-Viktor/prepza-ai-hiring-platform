#!/usr/bin/env bash
# Runs each service's integration tests (tests/integration) in a one-off container next to the
# running stack: real Postgres and Redis, but a "<service>_test" database and Redis database 15,
# so dev data is never touched. Usage: scripts/integration.sh [service...]
set -euo pipefail

cd "$(dirname "$0")/.."

if docker compose version >/dev/null 2>&1; then
  compose=(docker compose)
else
  compose=(docker-compose)
fi

services=("$@")

if [[ ${#services[@]} -eq 0 ]]; then
  services=(library generation rounds companies billing notifications ats api assistant)
fi

# Langfuse's keys emptied: tests trace nothing.
for service in "${services[@]}"; do
  echo "== $service"
  "${compose[@]}" run --rm --no-deps \
    -e INTEGRATION_TESTS=1 \
    -e REDIS_URL=redis://redis:6379/15 \
    -e LANGFUSE_PUBLIC_KEY= -e LANGFUSE_SECRET_KEY= \
    -v "$PWD/services/$service/tests:/services/$service/tests" \
    "$service" \
    uv run --no-sync --with pytest pytest -q tests/integration
done
