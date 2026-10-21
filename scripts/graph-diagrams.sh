#!/usr/bin/env bash
# Draws the LangGraph workflow diagrams from the compiled graphs and writes them into the docs
# between their `<!-- graph:<name> -->` markers (today: generation's graph in docs/generation.md).
# Run it after changing a graph; a unit test fails until the docs match. Needs nothing running.
# Usage: scripts/graph-diagrams.sh
set -euo pipefail

cd "$(dirname "$0")/../services/generation"

# The settings require these to import the graph; nothing connects to them.
FIREBASE_PROJECT_ID="demo-diagrams" \
  DATABASE_URL="postgresql://diagrams@localhost/diagrams" \
  REDIS_URL="redis://localhost" \
  LIBRARY_URL="http://library" \
  SERVICE_SECRET="diagrams-placeholder-secret-of-32-bytes" \
  uv run --quiet python -m app.jobs.graph_diagrams
