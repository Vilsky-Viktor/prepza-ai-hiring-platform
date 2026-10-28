#!/usr/bin/env bash
# Writes the OpenAPI description of each service the assistant's tools call into
# services/assistant/src/assistant/openapi/<service>.json, from the running stack's code
# (app.openapi(), which builds even where /openapi.json is off). The assistant builds its tools
# from these at startup; CI runs this and fails when a snapshot changed, so a changed route
# forces a refresh.
# Usage: scripts/assistant-openapi.sh   (with the stack up: docker compose up)
set -euo pipefail

cd "$(dirname "$0")/.."

if docker compose version >/dev/null 2>&1; then
  compose=(docker compose)
else
  compose=(docker-compose)
fi

# Only the routes and their schemas: the rest (servers, titles) can differ between machines.
script='
import json
import sys
from importlib import import_module

app = import_module(f"{sys.argv[1]}.main").app

if sys.argv[1] == "api":
    # The company API page'"'"'s routes are hidden from the public reference, but they are tools.
    from api.api.v1 import manage

    for route in manage.router.routes:
        route.include_in_schema = True

spec = app.openapi()
kept = {"paths": spec["paths"], "components": spec.get("components", {})}
print(json.dumps(kept, indent=1, ensure_ascii=False))
'

for service in companies billing library notifications ats api rounds accounts site; do
  echo "== $service"
  # Each service's package is named after it, but site's (site is a module of Python's own).
  package="$service"

  if [[ $service == site ]]; then
    package=site_content
  fi

  "${compose[@]}" exec -T "$service" uv run --no-sync python -c "$script" "$package" \
    > "services/assistant/src/assistant/openapi/$service.json"
done
