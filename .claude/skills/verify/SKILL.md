---
name: verify
description: Choose and run the right test suites for a change (unit, database, browser, end to end) and handle the slow local dev server. Use before calling any change done.
---

# Verify a change

Rule 8: every change ships with its tests, and the affected suites run before it's done.
For a change a user sees, only after the user has approved the UI (rule 14): a test run slows
the local site so much that the user can't review it meanwhile.

## Which suites

| What changed | Run |
|---|---|
| A service's code | `cd services/<svc> && uv run pytest -q tests/unit` |
| Anything touching the database, Redis or another service | `scripts/integration.sh <svc>` |
| `packages/common` | `cd packages/common && uv run pytest -q tests/unit`, plus every service that uses the changed code |
| Python style | `uvx ruff@0.16.10 check --fix services packages && uvx ruff@0.16.10 format services packages` |
| Frontend code | `cd frontend && npx tsc --noEmit -p . && npx eslint <files> && pnpm test` |
| Frontend texts | `cd frontend && node scripts/check-messages.mjs` |
| A signed-in screen or flow | `e2e_tests/signed-in.sh specs/<name>.spec.ts --retries=0` |
| A public page | `e2e_tests/pages.sh <name>.spec.ts --workers=1` |
| The whole hiring flow | `python3 e2e_tests/flow.py` (a real generation: a few cents of OpenAI) |
| Terraform | `docker run --rm -v "$PWD/infra/terraform:/tf" -w /tf hashicorp/terraform fmt -check` / `validate` |

Run a unit test's whole suite, not one file: fakes in other files often depend on what changed.

A prompt, model, effort, schema or output-shaping change also runs its eval (the `run-eval`
skill). Mechanics of browser tests (fixtures, locators, waits, retries):
`.claude/rules/testing.md`.

## What a test checks

The line (CLAUDE.md rule 8): does the text depend on what happened, or would it read the same
whatever happened?

- **Tested:** data (anything from input, the API or the database: names, emails, notes,
  amounts, counts, prices, grades, dates and their per-language formats); error and refusal
  messages, word for word ("That would take the available balance below zero."); whether a
  state-dependent element appears (a notification, toast, badge or notice), its kind (error or
  success) and the data it carries; an accessible name where it is the feature (an icon-only
  button's label).
- **Not tested:** fixed text that reads the same whatever happens: headings, labels,
  placeholders, descriptions, help texts, tooltips, empty-state sentences, the wording of
  success toasts and notices.

Find elements by role and position (`getByRole("main").getByRole("textbox")`, a dialog's
`spinbutton`, `.first()`), by structure (`a[href$="/billing"]`, a state attribute such as
`data-copied`), or by a `data-testid` added to the component when nothing else tells them
apart, never by fixed wording. A toast: `[data-sonner-toast][data-type="error"]` for its kind,
its text only when it's an error.

## The local dev server

The frontend is a Next.js dev server and compiles pages on first visit, so browser tests can
time out on cold pages. These are not code failures:

- Warm the pages a test opens first: `curl -s -m 180 -o /dev/null http://127.0.0.1:8090/<path>`.
- A `page.goto` timeout, `ERR_ABORTED`, a 502 or a 90-second `visit` timeout: run the test again.
- A failure at a different step on each run is timing; the same failure twice is real.
- When the frontend container passes about 6 GB (`docker stats --no-stream`), restart it:
  `/opt/homebrew/bin/docker-compose restart frontend`, then warm pages again.
- Browser runs queue: `pages.sh` and `signed-in.sh` run one at a time across every agent
  (`BROWSER_RUNS`, default 1); "waiting for another browser run" means one is in progress.
- If the frontend hangs on "Compiling" with long "filesystem cache" lines, its Turbopack cache
  has grown too large: stop the frontend, run
  `docker run --rm -v prepza_frontend-next:/next alpine rm -rf /next/dev`, and start it again.
- A run with no output for many minutes may be stuck: find it with
  `ps aux | grep signed-in.sh`, kill it, and run again.
- `pages.sh -g "a|b"` breaks on the pipe: run each name separately.

## Report

Say which suites ran and their counts, and name anything not checked (for example a path only
a production build can show).
