---
paths:
  - "e2e_tests/**"
  - "frontend/tests/**"
---

# Browser, vitest, load and smoke tests

Shared test rules are in `testing.md`; CLAUDE.md wins on any conflict.

## Vitest

- Covers `lib/`, hooks, constants and messages. Not adopted: component tests in vitest;
  components are covered by browser tests (rule 8).
- Fake timers (`vi.useFakeTimers`, `advanceTimersByTime`) instead of real delays.
- Test what a function returns or does, never its internal state.

## Browser, load and smoke tests

`e2e_tests/`: `pages/` (signed out), `signed-in/` (Auth emulator, `fixtures.ts`, `teardown.ts`),
`load/` (k6, never against production), `smoke.sh` (read-only, any environment), `flow.py` and
`mcp.py`; each suite runs in its Docker image through its script.

- One spec per screen or flow, named after it. Signed-in specs run in one worker in letter
  order, and each passes on its own.
- Tests own their data through fixtures and teardown (setup and cleanup together in a fixture,
  not in hooks); each test makes its own rows; repeated steps in `helpers/` (one module per
  area); no page objects (rule 4). Auth state is saved once (`storageState`).
- Locators as rule 8 (role and position first, `data-testid` last); web-first assertions
  (`await expect(locator)...`). Every promise is awaited; no floating promises.
- No fixed waits (`waitForTimeout`): wait for an element, a response or a state with
  auto-retrying `expect`, `expect.poll` or `toPass`. Time-dependent page code runs on
  `page.clock` (`install`, `fastForward`, `runFor`).
- No `networkidle`: wait for the element or response the step needs.
- A test that shows something never appears first waits for proof the page has loaded.
- Screenshots use `animations: "disabled"` instead of waiting for animations.
- Network is mocked only at the edges (`page.route`); no third-party sites. A mocked slow
  reply is held until the test releases it, never delayed by a timer.
- At most one retry; a pass on retry is flaky and gets fixed. Traces kept on failure
  (`retain-on-failure`); `forbidOnly: true`. Shard a suite only once it is long.

## Visual checks

- `toHaveScreenshot` catches layout regressions assertions miss, but its baselines depend on
  OS, browser and fonts and every intended change needs review. Not adopted: prepza takes
  review screenshots (`shot`) without comparing them.

## Accessibility

- `@axe-core/playwright` on key screens and states (tags `wcag2a`, `wcag2aa`), with known
  issues tracked rather than rules disabled; it is a new dev dependency, added only on the
  user's approval. Scans find about half of WCAG issues, so keyboard checks stay.

## Load and smoke

- k6 thresholds encode the SLOs (`http_req_failed`, `p(95)`) plus a threshold on `checks`
  (failed checks alone don't fail a run). Data made in `setup()` is deleted in `teardown()`.
- Capacity runs use an open model (arrival rate, `RATE`), watching `dropped_iterations`; what
  else load tests decide: `.claude/rules/scalability.md`.
- Smoke is minimal and read-only, run after each deploy and before heavier runs.

Research (local notes, git-ignored): `internal_docs/testing-best-practices.md`.
