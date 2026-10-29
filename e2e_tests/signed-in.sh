#!/usr/bin/env bash
# Browser tests of the signed-in pages (e2e_tests/signed-in), in Playwright's Docker image,
# against the running local stack, on the gateway's test port (8082: the production build of the
# frontend, test_frontend.sh). Users sign in through the Firebase Auth emulator's own sign-in
# page, so this runs only where the emulator is set up (NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_URL).
# Every test makes its own throwaway users, companies and interviews. Results land in
# e2e_tests/signed-in/test-results/<run> (screenshots in its screenshots/), one folder per run.
# Usage: e2e_tests/signed-in.sh [playwright args], e.g. specs/b-candidate.spec.ts; WORKERS=n sets
# how many tests run at once (default 3).
set -euo pipefail

cd "$(dirname "$0")/.."

# A run of every spec, or of a spec with a @global test, has the stack to itself: those tests turn
# on what every page sees (maintenance mode, the pause, a limit). A run of named specs without one
# shares it. A spec named in a way not found here counts as global.
alone=" alone"
specs=()

for arg in "$@"; do
  if [[ "$arg" == *.spec.ts || "$arg" == *.spec.ts:* ]]; then
    specs+=("e2e_tests/signed-in/${arg%%:*}")
  fi
done

if ((${#specs[@]})); then
  grep -qs "@global" "${specs[@]}" && found=0 || found=$?

  if ((found == 1)); then
    alone=""
  fi
fi

# The tests open a production build of the frontend (test_frontend.sh), never the dev server.
# At most BROWSER_RUNS browser runs at once on the local stack, whoever starts them, all of the
# same frontend files (browser_lock.py); the slot is freed when this script exits. The test site
# is then rebuilt if the frontend changed since its last build.
source="$(e2e_tests/test_frontend.sh --source)"
browser_slot="$(python3 e2e_tests/browser_lock.py "$$" "$source$alone")"
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
# The tests run in parallel first; then, in a run that has the stack to itself, the @global ones
# (the `global` project), one at a time with nothing else running. Each phase has its own results
# folder, as Playwright empties it when it starts.
COPYFILE_DISABLE=1 tar -C "$tests" --no-xattrs --exclude node_modules --exclude test-results -cf - . |
  docker run -i --rm --name "$container" --ipc=host --network "$network" \
    -v "$results:/tests/test-results" \
    -v "$PWD/.env:/env/.env:ro" \
    -w /tests \
    -e SITE_URL=http://localhost:8090 \
    -e API_URL=http://gateway:8082/api \
    -e FRONTEND_URL=http://gateway:8082 \
    -e HOST_RULES="MAP localhost:8090 gateway:8082, MAP $emulator firebase-auth:9199" \
    -e FORWARDS="8090=gateway:8082,${emulator##*:}=firebase-auth:9199" \
    -e GLOBAL="${alone:+1}" \
    -e WORKERS \
    mcr.microsoft.com/playwright:v1.63.0-noble@sha256:eff16c30e6f3f4af0a03fa4b706120d5e9b0891c344a27d64559aff5900a4a27 \
    sh -c '
      tar -xf - && npm ci --no-audit --no-fund --loglevel=error || exit 1
      npx playwright test --project=chromium --project=firefox --project=webkit \
        --output=test-results/parallel "$@"
      parallel=$?
      [ -z "$GLOBAL" ] && exit "$parallel"
      npx playwright test --project=global --pass-with-no-tests --output=test-results/global "$@"
      exit $((parallel | $?))
    ' sh "$@" ||
  status=$?

echo "Results: ${results#"$PWD"/}"
exit "${status:-0}"
