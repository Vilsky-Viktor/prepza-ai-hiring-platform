#!/usr/bin/env bash
# Runs each service's integration tests (tests/integration) in a one-off container next to the
# running stack: real Postgres and Redis, but a "<service>_test" database and Redis database 15,
# so dev data is never touched. Usage: scripts/integration.sh [service...]
# PYTEST_ADDOPTS reaches pytest: PYTEST_ADDOPTS=--reverse runs the tests in reverse order
# (pytest-reverse), to check that none depends on another's leftovers.
set -euo pipefail

cd "$(dirname "$0")/.."

if docker compose version >/dev/null 2>&1; then
  compose=(docker compose)
else
  compose=(docker-compose)
fi

services=("$@")

if [[ ${#services[@]} -eq 0 ]]; then
  services=(library generation rounds companies billing notifications ats api assistant accounts site)
fi

# Tests make and drop their "<service>_test" database and create extensions in it, which a
# service's own user may not (it owns only its database), so they run as the local admin.
password="${POSTGRES_PASSWORD:-$(grep -E '^POSTGRES_PASSWORD=' .env | cut -d= -f2-)}"

# Langfuse's keys emptied: tests trace nothing. The shared test helpers (packages/common/tests:
# the fake Redis, the fixtures that keep tests from publishing) are mounted as they are now.
for service in "${services[@]}"; do
  echo "== $service"
  "${compose[@]}" run --rm --no-deps \
    -e INTEGRATION_TESTS=1 \
    -e DATABASE_URL="postgresql://prepza:${password}@postgres:5432/${service}" \
    -e REDIS_URL=redis://redis:6379/15 \
    -e LANGFUSE_PUBLIC_KEY= -e LANGFUSE_SECRET_KEY= \
    -e PYTEST_ADDOPTS \
    -v "$PWD/services/$service/tests:/services/$service/tests" \
    -v "$PWD/packages/common/tests:/packages/common/tests:ro" \
    "$service" \
    uv run --no-sync --with pytest==9.1.1 --with pytest-reverse==1.9.0 pytest -q tests/integration
done
