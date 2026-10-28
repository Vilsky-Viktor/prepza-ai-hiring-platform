#!/usr/bin/env bash
# What changed, for CI's `changes` job (.github/workflows/ci.yml): the parts to test and build,
# whether the whole-stack tests run, and the commit compared with.
# A pull request compares with its base (PR_BASE); main with the last commit CI passed on
# (through `gh api`, GH_TOKEN and GITHUB_REPOSITORY). Each service also depends on
# packages/common; a change to CI itself or the Python version counts as everything.
# Writes changed, stack and base to $GITHUB_OUTPUT (stdout when it isn't set).
# Locally: PR_BASE=origin/main scripts/ci_changes.sh
set -euo pipefail

services="library generation rounds companies billing notifications ats api assistant accounts site"
everything="$services frontend common"
base="${PR_BASE:-}"
files=""

if [[ -z "$base" ]]; then
  base="$(gh api "repos/${GITHUB_REPOSITORY:?set GITHUB_REPOSITORY (owner/name) or PR_BASE}/actions/workflows/ci.yml/runs?branch=main&event=push&status=success&per_page=1" --jq '.workflow_runs[0].head_sha // ""')"
fi

# No earlier passing commit to build on: everything.
if [[ -z "$base" ]] || ! git merge-base --is-ancestor "$base" HEAD; then
  base=""
  changed="$everything"
else
  files="$(git diff --name-only "$base" HEAD)"
  changed=""

  if grep -qE '^(\.github/workflows/ci\.yml|\.python-version|scripts/ci_changes\.sh)$' <<< "$files"; then
    changed="$everything"
  else
    for name in $services; do
      if grep -qE "^(services/$name|packages/common)/" <<< "$files"; then
        changed="$changed $name"
      fi
    done

    if grep -q '^frontend/' <<< "$files"; then
      changed="$changed frontend"
    fi

    # site serves the site's guide articles from its image.
    if grep -qE '^frontend/content/([a-z]+/)?guides/' <<< "$files"; then
      changed="$changed site"
    fi

    if grep -q '^packages/common/' <<< "$files"; then
      changed="$changed common"
    fi
  fi
fi

# The whole-stack tests run when any part, or the stack and its tests, changed.
stack=false

if [[ -n "$changed" ]] || grep -qE '^(e2e_tests|gateway|database|firebase|scripts|compose)/|^docker-compose\.yml$' <<< "$files"; then
  stack=true
fi

echo "Since ${base:-the start}: ${changed:-nothing}" >&2
{
  echo "changed=$(jq -nc --arg names "$changed" '$names | split(" ") | map(select(. != ""))')"
  echo "stack=$stack"
  echo "base=$base"
} >> "${GITHUB_OUTPUT:-/dev/stdout}"
