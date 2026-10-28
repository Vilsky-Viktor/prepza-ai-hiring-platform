#!/usr/bin/env bash
# Browser tests of the signed-out pages (e2e_tests/pages), in Playwright's Docker image, against
# the running stack: the browser opens SITE_URL, which Chromium resolves to the gateway on the
# stack's own network. Tests that need templates add their own straight into the library database
# (POSTGRES_PASSWORD from .env, mounted read-only) and delete them after, so the platform's own
# templates are never read or changed.
# Results land in e2e_tests/pages/test-results/<run>, one folder per run.
# Usage: e2e_tests/pages.sh [playwright args], e.g. --workers=2
set -euo pipefail

cd "$(dirname "$0")/.."

# One browser run at a time on the local stack (BROWSER_RUNS), whoever starts it; the slot is
# freed when this script exits.
browser_slot="$(python3 e2e_tests/browser_lock.py "$$")"
trap 'rm -rf "$browser_slot"' EXIT

if docker compose version >/dev/null 2>&1; then
  compose=(docker compose)
else
  compose=(docker-compose)
fi

gateway="$("${compose[@]}" ps -q gateway)"
network="$(docker inspect -f '{{range $name, $_ := .NetworkSettings.Networks}}{{$name}}{{end}}' "$gateway")"

# The secret that signs emails' unsubscribe links, as notifications has it (compose's default when
# .env has none), passed by name so it's never printed or put on the command line.
EMAIL_LINK_SECRET="$(sed -n 's/^EMAIL_LINK_SECRET=//p' .env 2>/dev/null)"
export EMAIL_LINK_SECRET="${EMAIL_LINK_SECRET:-local-email-link-secret}"

tests="$PWD/e2e_tests/pages"
# Each run's results (traces, screenshots) in a folder of its own: Playwright empties its results
# folder when a run starts, so runs at the same time would delete each other's. A week's are kept.
run="$(date +%Y%m%d-%H%M%S)-$$"
results="$tests/test-results/$run"
mkdir -p "$results"
find "$tests/test-results" -mindepth 1 -maxdepth 1 -type d -mtime +7 -exec rm -rf {} +

# The specs go in through a tar stream rather than a mount, so each run installs its own packages
# (two runs sharing a mounted node_modules break each other's) and sees the files as they are now
# (Docker Desktop's file sharing can serve a file edited moments before as it was).
COPYFILE_DISABLE=1 tar -C "$tests" --no-xattrs --exclude node_modules --exclude test-results -cf - . |
  docker run -i --rm --network "$network" \
    -v "$results:/tests/test-results" -w /tests \
    -v "$PWD/.env:/env/.env:ro" \
    -e EMAIL_LINK_SECRET \
    -e SITE_URL=http://localhost:8090 \
    -e HOST_RULES="MAP localhost:8090 gateway:80" \
    -e REQUEST_URL=http://gateway \
    mcr.microsoft.com/playwright:v1.63.0-noble@sha256:eff16c30e6f3f4af0a03fa4b706120d5e9b0891c344a27d64559aff5900a4a27 \
    sh -c 'tar -xf - && npm ci --no-audit --no-fund --loglevel=error && npx playwright test "$@"' sh "$@" ||
  status=$?

echo "Results: ${results#"$PWD"/}"
exit "${status:-0}"
