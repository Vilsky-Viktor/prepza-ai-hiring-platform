#!/usr/bin/env bash
# Makes the landing's sample reports again (frontend/public/samples/prepza-report-samples.zip):
# the report of all candidates and one candidate's report, made by the app's own PDF export from
# the made-up data in frontend/src/constants/report-samples-fixture.ts. Run it when the reports'
# design changes. Needs the local stack running (the development page /report-samples).
# Usage: scripts/report-samples.sh
set -euo pipefail

cd "$(dirname "$0")/.."

if docker compose version >/dev/null 2>&1; then
  compose=(docker compose)
else
  compose=(docker-compose)
fi

gateway="$("${compose[@]}" ps -q gateway)"
network="$(docker inspect -f '{{range $name, $_ := .NetworkSettings.Networks}}{{$name}}{{end}}' "$gateway")"
out="$(mktemp -d)"
trap 'rm -rf "$out"' EXIT

# The browser keeps the site's own address, pointed at the gateway, as the browser tests do.
docker run --rm --network "$network" \
  -v "$PWD/frontend/scripts/report-samples.mjs:/work/report-samples.mjs:ro" \
  -v "$out:/out" -w /work \
  -e npm_config_update_notifier=false \
  -e HOST_RULES="MAP localhost:8090 gateway:80" \
  mcr.microsoft.com/playwright:v1.63.0-noble \
  sh -c "npm i --no-save --no-audit --no-fund --loglevel=error playwright@1.63.0 >/dev/null && node report-samples.mjs /out"

zip="$PWD/frontend/public/samples/prepza-report-samples.zip"
mkdir -p "$(dirname "$zip")"
rm -f "$zip"
# No folders and no extra file attributes, so the ZIP holds just the two PDFs.
(cd "$out" && zip -q -X -j "$zip" prepza-sample-candidates.pdf prepza-sample-candidate-report.pdf)
echo "Made ${zip#"$PWD"/}"
