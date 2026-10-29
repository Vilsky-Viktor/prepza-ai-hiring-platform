#!/usr/bin/env bash
# The browser tests' site: a production build of the frontend (compose's `frontend-test`, behind
# the gateway's port 8082), so tests never wait on the dev server compiling pages and never slow
# down the site the developer browses (port 8090). Only the browser test scripts call this.
#
#   e2e_tests/test_frontend.sh --source    prints a hash of the frontend's files as they are now
#                                          (uncommitted changes too) and the settings baked in
#   e2e_tests/test_frontend.sh <source>    rebuilds and restarts the test site unless it already
#                                          runs that source, and waits until it answers
#
# The scripts take their browser slot (browser_lock.py) between the two, so the site is never
# rebuilt under a run of another source. One build at a time: a run that finds another building
# waits for it, then finds the site already up to date.
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ "${1:-}" == "--source" ]]; then
  # The files the image is built from (frontend/tests aren't, .dockerignore) and the build's
  # NEXT_PUBLIC_* settings; values go into the hash only, never printed.
  {
    git ls-files -co --exclude-standard -z frontend | grep -zv '^frontend/tests/' | xargs -0 shasum
    grep -E '^(NEXT_PUBLIC_[A-Z_]*|ENVIRONMENT)=' .env 2>/dev/null || true
  } | shasum | cut -c1-16
  exit 0
fi

source="${1:?usage: e2e_tests/test_frontend.sh --source | <source>}"

if docker compose version >/dev/null 2>&1; then
  compose=(docker compose)
else
  compose=(docker-compose)
fi

lock="$(git rev-parse --git-common-dir)/prepza-browser-runs/build"
mkdir -p "$(dirname "$lock")"

# The build lock holds the builder's pid; a lock whose builder is gone is taken over.
until mkdir "$lock" 2>/dev/null; do
  holder="$(cat "$lock/pid" 2>/dev/null || true)"

  if [[ -n "$holder" ]] && ! kill -0 "$holder" 2>/dev/null; then
    rm -rf "$lock"
  fi

  sleep 2
done

echo "$$" >"$lock/pid"
trap 'rm -rf "$lock"' EXIT

container="$("${compose[@]}" --profile test ps -q frontend-test 2>/dev/null || true)"
built=""

if [[ -n "$container" ]]; then
  built="$(docker inspect -f '{{index .Config.Labels "prepza.frontend-source"}} {{.State.Running}}' "$container")"
fi

if [[ "$built" != "$source true" ]]; then
  echo "building the test frontend (production build of the current files, a few minutes)" >&2
  started=$SECONDS
  FRONTEND_TEST_SOURCE="$source" "${compose[@]}" --profile test up -d --build --wait --quiet-build \
    frontend-test >&2
  echo "test frontend built and started in $((SECONDS - started))s" >&2
fi
