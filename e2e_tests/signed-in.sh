#!/usr/bin/env bash
# Browser tests of the signed-in pages (e2e_tests/signed-in), in Playwright's Docker image,
# against the running local stack. Users sign in through the Firebase Auth emulator's own sign-in
# page, so this runs only where the emulator is set up (NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_URL).
# Every test makes its own throwaway users, companies and interviews. Results land in
# e2e_tests/signed-in/test-results/<run> (screenshots in its screenshots/), one folder per run.
# Usage: e2e_tests/signed-in.sh [playwright args]
set -euo pipefail

cd "$(dirname "$0")/.."

# One browser run at a time on the local stack (BROWSER_RUNS), whoever starts it.
# shellcheck source=browser-lock.sh
. e2e_tests/browser-lock.sh
take_browser_slot

if docker compose version >/dev/null 2>&1; then
  compose=(docker compose)
else
  compose=(docker-compose)
fi

gateway="$("${compose[@]}" ps -q gateway)"
network="$(docker inspect -f '{{range $name, $_ := .NetworkSettings.Networks}}{{$name}}{{end}}' "$gateway")"

# The emulator's host and port as the browser knows them, read without printing the setting.
emulator="$(sed -n 's/^NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_URL=//p' .env | sed -E 's#^[a-z]+://##; s#/.*$##')"

if [[ -z "$emulator" ]]; then
  echo "NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_URL isn't set: these tests sign in through the emulator" >&2
  exit 1
fi

tests="$PWD/e2e_tests/signed-in"
# Each run's results (traces, screenshots) in a folder of its own: Playwright empties its results
# folder when a run starts, so runs at the same time would delete each other's. A week's are kept.
run="$(date +%Y%m%d-%H%M%S)-$$"
results="$tests/test-results/$run"
mkdir -p "$results"
find "$tests/test-results" -mindepth 1 -maxdepth 1 -type d -mtime +7 -exec rm -rf {} +

# The specs go in through a tar stream rather than a mount: Docker Desktop's file sharing can
# serve a file edited moments before as it was. Results and screenshots come back through a mount.
# --ipc=host: Chromium's shared memory, as Playwright advises for Docker (pages crash without it).
COPYFILE_DISABLE=1 tar -C "$tests" --no-xattrs --exclude node_modules --exclude test-results -cf - . |
  docker run -i --rm --ipc=host --network "$network" \
    -v "$results:/tests/test-results" \
    -v "$PWD/.env:/env/.env:ro" \
    -w /tests \
    -e SITE_URL=http://localhost:8090 \
    -e API_URL=http://gateway/api \
    -e HOST_RULES="MAP localhost:8090 gateway:80, MAP $emulator firebase-auth:9199" \
    -e FORWARDS="8090=gateway:80,${emulator##*:}=firebase-auth:9199" \
    mcr.microsoft.com/playwright:v1.63.0-noble \
    sh -c 'tar -xf - && npm ci --no-audit --no-fund --loglevel=error && npx playwright test "$@"' sh "$@" ||
  status=$?

echo "Results: ${results#"$PWD"/}"
exit "${status:-0}"
