---
paths:
  - "services/**"
  - "packages/**"
  - "frontend/**"
  - "e2e_tests/**"
  - "evals/**"
  - "infra/**"
  - "compose/**"
  - "gateway/**"
  - "scripts/**"
  - ".github/**"
  - ".claude/**"
  - "docs/**"
---

# File and function size

CLAUDE.md rule 2 sets the limits; this is how to meet them.

## Files

- 300 lines (`wc -l`, blank lines and comments included) is a trigger to look for a seam, not a
  target: split by responsibility, one reason to change per file (rule 3), never at an arbitrary
  line, and never into pieces that can only be read together ("conjoined" modules).
- Seams that work here: a long router's handlers into a `services/` module; a component's
  sub-components or pure helpers into their own files (`lib/`); tests by area, mirroring the code;
  Terraform by kind of resource; a workflow's inline shell into `scripts/`; CSS by concern
  (`animations.css`).
- Splitting the opposite way is a smell too: one concept scattered across many files means one
  change touches all of them. Merge back when that happens.
- Exempt (regenerated or data, never read as code): lockfiles, OpenAPI snapshots,
  `frontend/src/types/api/`, `frontend/messages/`, page guides, `templates/languages/`,
  `evals/datasets/`, fixtures, binary files, articles in `frontend/content/`. Tests are not exempt.
- `scripts/check_file_size.sh` is the check; run it before committing. A new exempt kind is added
  there and to rule 2 in the same change.

## Functions

- A function does one thing at one level of abstraction. Length alone is rarely a reason to split
  (Ousterhout); a function over about 50 lines (Python) or a screen of logic (TypeScript, markup
  aside) is a prompt to look for a seam, not a rule.
- Complexity is the enforced limit: at most 15 (Ruff `C901` in `ruff.toml`, ESLint `complexity` in
  `frontend/eslint.config.mjs`), 12 branches and 50 statements in Python (`PLR0912`, `PLR0915`).
  Tests' fakes and migrations are exempt. Lower complexity by early returns, a lookup table instead
  of a branch chain, or pulling a step into a named function.
- Not adopted: ESLint `max-lines-per-function` (flags JSX markup, not logic) and Ruff `PLR0913`
  (FastAPI routes take injected dependencies as arguments).
- A temporary exemption names the function, carries `TODO(rule 2)` and is removed with the next
  change to that file.

## Files agents read

- Context degrades as it grows ("context rot"): give agents the smallest set of high-signal text.
- CLAUDE.md under 200 lines; area rules in `.claude/rules/`, one topic per file, each with
  `paths:`, under about 150 lines (split rather than drop a practice); a SKILL.md under 500 lines,
  references one level deep; a doc or reference file past 100 lines starts with its contents.

Research (local notes, git-ignored): `internal_docs/best-practices/file-size.md`.
