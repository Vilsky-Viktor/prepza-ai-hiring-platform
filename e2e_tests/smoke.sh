#!/usr/bin/env bash
# Hits the public pages and service health endpoints through the gateway.
set -euo pipefail

base="${1:-http://localhost:8090}"

check() {
  local path="$1"
  local code

  code="$(curl -sS -o /dev/null -w '%{http_code}' "$base$path")"

  if [[ "$code" != "200" ]]; then
    echo "FAIL $path -> $code" >&2

    exit 1
  fi

  echo "ok $path"
}

check /
check /companies
check /api/library/ready
check /api/generate/ready
check /api/rounds/ready
check /api/companies/ready
check /api/billing/ready
check /api/ats/ready
check /api/v1/ready
check /api/assistant/ready
check /api/notifications/ready
check /api/accounts/ready
# AI apps reach the assistant at the site's root (MCP and its OAuth server).
check /.well-known/oauth-authorization-server
check /.well-known/oauth-protected-resource/mcp

# The site doesn't say what it runs on.
if curl -sSI "$base/" | grep -qi '^x-powered-by:'; then
  echo "FAIL / sends X-Powered-By" >&2

  exit 1
fi

echo "ok no X-Powered-By"

echo "smoke ok"
