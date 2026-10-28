#!/usr/bin/env bash
# Fails when a hand-written tracked file has more than 300 lines (CLAUDE.md rule 2), counting
# all lines as `wc -l` does. Generated files, data, binary files and articles are exempt.
# Usage: scripts/check_file_size.sh (from anywhere in the repo; reads nothing but git's files).
set -euo pipefail

limit=300

# Rule 2's exempt kinds: generated files, data, and the site's articles.
exempt='(^|/)(uv\.lock|pnpm-lock\.yaml)$'
exempt+='|^services/assistant/src/assistant/openapi/'
exempt+='|^frontend/src/types/api/'
exempt+='|^frontend/messages/'
exempt+='|^services/rounds/src/rounds/page_guides/'
exempt+='|^services/notifications/src/notifications/templates/languages/'
exempt+='|^evals/datasets/'
exempt+='|(^|/)fixtures/'
exempt+='|^frontend/content/'

cd "$(git rev-parse --show-toplevel)"

files=()

while IFS= read -r -d '' path; do
  if [[ -f "$path" && ! -L "$path" && ! "$path" =~ $exempt ]]; then
    files+=("$path")
  fi
done < <(git ls-files -z)

over=0

# One wc for every file; its last line is the total.
while read -r lines path; do
  # Binary files are exempt: grep -I finds no text in them.
  if (( lines > limit )) && [[ "$path" != total ]] && grep -Iq '' "$path"; then
    echo "$path: $lines lines (limit $limit)" >&2
    over=1
  fi
done < <(wc -l "${files[@]}")

if (( over )); then
  echo "Split each file above at a seam (CLAUDE.md rule 2)." >&2
fi

exit "$over"
