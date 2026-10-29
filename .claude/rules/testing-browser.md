---
paths:
  - "e2e_tests/**"
  - "frontend/tests/**"
---

# Browser, vitest, load and smoke tests

Shared test rules are in `testing.md`; CLAUDE.md wins on any conflict.

## Vitest

- Covers `lib/`, hooks, `config/` and messages. Not adopted: component tests in vitest;
  components are covered by browser tests (rule 8).
- Fake timers (`vi.useFakeTimers`, `advanceTimersByTime`) instead of real delays.
- Test what a function returns or does, never its internal state.

## Browser, load and smoke tests

`e2e_tests/`: `pages/` (signed out), `signed-in/` (Auth emulator, `fixtures.ts`, `teardown.ts`),
`load/` (k6, never against production), `smoke.sh` (read-only, any environment), `flow.py` and
`mcp.py`; each suite runs in its Docker image through its script. Browser suites open a
production build of the frontend (`frontend-test`, the gateway's port 8082), never the dev server.

- One spec per screen or flow, named after it. Tests run in parallel, in any order, and each
  passes on its own; a test that changes what every page sees (maintenance mode, the pause, a
  global limit) is tagged `@global` and runs after the others, alone.
- Tests own their data through fixtures and teardown (setup and cleanup together in a fixture,
  not in hooks); each test makes its own rows; repeated steps in `helpers/` (one module per
  area); no page objects (rule 4). Signing in goes through the UI only in the tests of signing
  in; every other test signs its own user in at the Auth emulator's API and opens a fresh
  context with that session (`storageState`).
- A viewport plays no part in most checks: the signed-out suite's phone project runs only tests
  tagged `@phone` (or `@phone-only`), where the phone's layout differs.
- Checks of data that a lower level can make (every language's messages, every currency) go to
  vitest or the service's tests, with one or two browser cases left for the screen.
- Locators as rule 8 (role and position first, `data-testid` last); a text, test id or CSS
  locator on a streamed page takes the visible one (`.filter({ visible: true })`: React parks
  streamed parts in a hidden copy first, `docs/browser-tests.md`); web-first assertions
  (`await expect(locator)...`). Every promise is awaited; no floating promises.
- No fixed waits (`waitForTimeout`): wait for an element, a response or a state with
  auto-retrying `expect`, `expect.poll` or `toPass`. Time-dependent page code runs on
  `page.clock` (`install`, `fastForward`, `runFor`).
- No `networkidle`: wait for the element or response the step needs.
- A test that shows something never appears first waits for proof the page has loaded.
- Screenshots use `animations: "disabled"` instead of waiting for animations. Review screenshots
  (`shot`) are taken only with `SHOTS=1`.
- Network is mocked only at the edges (`page.route`); no third-party sites. A mocked slow
  reply is held until the test releases it, never delayed by a timer.
- At most one retry; a pass on retry is flaky and gets fixed. Traces kept on failure
  (`retain-on-failure`); `forbidOnly: true`. Shard a suite only once it is long.

## Visual checks

- `toHaveScreenshot` catches layout regressions assertions miss, but its baselines depend on
  OS, browser and fonts and every intended change needs review. Not adopted: prepza takes
  review screenshots (`shot`) without comparing them.

## Accessibility

- `@axe-core/playwright` on key screens and states (tags `wcag2a`, `wcag2aa`; the signed-out
  pages WCAG 2.2 AA), signed out (`accessibility.spec.ts`) and signed in
  (`y-accessibility.spec.ts`), with known issues tracked in a list beside the check rather than
  rules disabled. Scans find about half of WCAG issues, so keyboard checks stay.

## Load and smoke

- k6 thresholds encode the SLOs (`http_req_failed`, `p(95)`) plus a threshold on `checks`
  (failed checks alone don't fail a run). Data made in `setup()` is deleted in `teardown()`.
- Capacity runs use an open model (arrival rate, `RATE`), watching `dropped_iterations`; what
  else load tests decide: `.claude/rules/scalability.md`.
- Smoke is minimal and read-only, run after each deploy and before heavier runs.

Research (local notes, git-ignored): `internal_docs/best-practices/testing.md`.
