#!/usr/bin/env bash
# Load tests (e2e_tests/load) with k6, in its Docker image, against the running local stack: k6
# joins the stack's network and calls the gateway by name. Throwaway users come from the Firebase
# Auth emulator, so the signed-in scenarios run only locally; never point this at production.
# Afterwards every throwaway account (and with it its companies) is deleted and the databases are
# checked for anything left.
#
# Usage: e2e_tests/load.sh candidates|dashboard|public|clean [--i-mean-it]
# Settings (environment): VUS, RATE, DURATION, ITERATIONS, THINK_SECONDS, COMPANIES, TEMPLATE_ID, PAGES,
# BASE_URL (default http://gateway:8081, the gateway's port without the per-IP limit; another host
# than the local stack's needs --i-mean-it).
set -euo pipefail

cd "$(dirname "$0")/.."

scenario="${1:-}"
base_url="${BASE_URL:-http://gateway:8081}"
host="$(echo "$base_url" | sed -E 's#^[a-z]+://##; s#[:/].*$##')"

case "$scenario" in
  candidates | dashboard | public | clean) ;;
  *)
    echo "usage: e2e_tests/load.sh candidates|dashboard|public|clean [--i-mean-it]" >&2
    exit 2
    ;;
esac

case "$host" in
  gateway | localhost | 127.0.0.1 | host.docker.internal) ;;
  *)
    # Users come from the local Auth emulator: elsewhere only signed-out visitors can be loaded.
    if [ "$scenario" != "public" ]; then
      echo "only the public scenario runs against another host than the local stack" >&2
      exit 2
    fi

    if [ "${2:-}" != "--i-mean-it" ]; then
      echo "$base_url isn't the local stack: add --i-mean-it if it really is a test environment" >&2
      echo "(never production: the run makes users and companies and loads every service)" >&2
      exit 2
    fi
    ;;
esac

if docker compose version >/dev/null 2>&1; then
  compose=(docker compose)
else
  compose=(docker-compose)
fi

gateway="$("${compose[@]}" ps -q gateway)"
network="$(docker inspect -f '{{range $name, $_ := .NetworkSettings.Networks}}{{$name}}{{end}}' "$gateway")"
# Read without printing the setting.
project="$(sed -n 's/^FIREBASE_PROJECT_ID=//p' .env)"

k6() {
  # The scripts go in through a tar stream rather than a mount, as in signed-in.sh: Docker
  # Desktop's file sharing can serve a file edited moments before as it was.
  COPYFILE_DISABLE=1 tar -C e2e_tests/load --no-xattrs -cf - --exclude README.md . |
    docker run -i --rm --network "$network" \
      -e BASE_URL="$base_url" -e FIREBASE_PROJECT_ID="$project" \
      -e VUS -e RATE -e DURATION -e ITERATIONS -e THINK_SECONDS -e COMPANIES -e TEMPLATE_ID -e PAGES \
      --entrypoint sh grafana/k6:2.3.0 \
      -c "mkdir -p /tmp/load && tar -xf - -C /tmp/load && cd /tmp/load && k6 run --quiet $1"
}

status=0

if [ "$scenario" != "clean" ]; then
  k6 "$scenario.js" || status=$?
fi

if [ "$scenario" != "public" ]; then
  # Events still on their way (a candidate finished...) land before the clean-up.
  sleep 5
  ids="$(e2e_tests/load/leftovers.sh ids)"
  k6 clean.js || status=$?
  # Deleted companies' notifications go through an event (company.deleted).
  sleep 3
  e2e_tests/load/leftovers.sh count "$ids" || status=$?
fi

exit "$status"
