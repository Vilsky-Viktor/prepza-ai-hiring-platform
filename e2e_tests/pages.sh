#!/usr/bin/env bash
# Browser tests of the signed-out pages (e2e_tests/pages), in Playwright's Docker image, against
# the running stack: the browser opens SITE_URL, which Chromium resolves to the gateway's test port
# (8082: the production build of the frontend, test_frontend.sh) on the stack's own network.
# Tests that need templates add their own straight into the library database (POSTGRES_PASSWORD
# from .env, mounted read-only) and delete them after, so the platform's own templates are never
# read or changed.
# Results land in e2e_tests/pages/test-results/<run>, one folder per run.
# Usage: e2e_tests/pages.sh [playwright args], e.g. faq.spec.ts; WORKERS=n sets how many tests run
# at once (default 3); SHOTS=1 takes the review screenshots.
set -euo pipefail

cd "$(dirname "$0")/.."

# The tests open a production build of the frontend (test_frontend.sh), never the dev server.
# At most BROWSER_RUNS browser runs at once on the local stack, whoever starts them, all of the
# same frontend files (browser_lock.py); the slot is freed when this script exits. The test site
# is then rebuilt if the frontend changed since its last build.
source="$(e2e_tests/test_frontend.sh --source)"
browser_slot="$(python3 e2e_tests/browser_lock.py "$$" "$source")"
# The browsers' container is named after this script, so stopping the script stops it too.
container="prepza-browser-tests-$$"
trap 'rm -rf "$browser_slot"; docker rm -f "$container" >/dev/null 2>&1 || true' EXIT
e2e_tests/test_frontend.sh "$source"

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
  docker run -i --rm --name "$container" --network "$network" \
    -v "$results:/tests/test-results" -w /tests \
    -v "$PWD/.env:/env/.env:ro" \
    -e EMAIL_LINK_SECRET \
    -e SITE_URL=http://localhost:8090 \
    -e HOST_RULES="MAP localhost:8090 gateway:8082" \
    -e REQUEST_URL=http://gateway:8082 \
    -e WORKERS \
    -e SHOTS \
    mcr.microsoft.com/playwright:v1.64.1-noble@sha256:47b510dd9230bf0b9bfc9b20102241e577ea7a99334ab4c3ca19f19770e9b8ea \
    sh -c 'tar -xf - && npm ci --no-audit --no-fund --loglevel=error && npx playwright test "$@"' sh "$@" ||
  status=$?

echo "Results: ${results#"$PWD"/}"
exit "${status:-0}"
