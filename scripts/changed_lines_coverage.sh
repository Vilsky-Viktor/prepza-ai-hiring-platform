#!/usr/bin/env bash
# How much of the lines a change touches its unit tests run: diff-cover on a coverage report,
# compared with BASE (CI's `changes` job: the pull request's base, or the last commit CI passed
# on). Fails under CHANGED_LINES_COVERAGE percent (60: storage code is covered by the
# integration suites, which this doesn't count). The report goes to the job's summary in CI.
# Usage, from the project's folder: BASE=origin/main scripts/changed_lines_coverage.sh coverage.xml
set -euo pipefail

report="$1"
threshold="${CHANGED_LINES_COVERAGE:-60}"
version="10.6.0"
summary="${RUNNER_TEMP:-/tmp}/changed-lines-coverage.md"

if [[ -z "${BASE:-}" ]]; then
  echo "No commit to compare with (everything changed): no changed-lines report." >&2
  exit 0
fi

if command -v uvx >/dev/null; then
  diff_cover=(uvx "diff-cover@$version")
else
  diff_cover=(pipx run "diff-cover==$version")
fi

status=0
"${diff_cover[@]}" "$report" --compare-branch="$BASE" --fail-under="$threshold" \
  --markdown-report "$summary" || status=$?

if [[ -n "${GITHUB_STEP_SUMMARY:-}" && -f "$summary" ]]; then
  cat "$summary" >> "$GITHUB_STEP_SUMMARY"
fi

exit "$status"
