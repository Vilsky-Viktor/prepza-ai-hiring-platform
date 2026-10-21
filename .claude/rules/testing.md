---
paths:
  - "services/*/tests/**"
  - "packages/common/tests/**"
  - "frontend/tests/**"
  - "e2e_tests/**"
  - "evals/**"
  - "scripts/integration.sh"
  - "**/conftest.py"
  - "**/playwright.config.ts"
  - "frontend/vitest.config.*"
---

# Tests

What a test checks and where it lives is rule 8; these are the mechanics every suite shares.
Python tests: `testing-backend.md`; vitest and browser, load and smoke tests:
`testing-browser.md`. CLAUDE.md wins on any conflict.

## What goes at which level

- Many fast low-level tests, few end-to-end ones; move a check down when a lower level can
  make it. For UI and API code, most confidence comes from tests that use the software the way
  it is used (an endpoint through its route, a screen in the browser).
- Size by what a test may touch: unit = small (one process, no network or disk),
  `tests/integration` = medium (localhost, a database, Redis, emulators), `e2e_tests` = large
  (end to end). Every size can run in parallel.

## No fixed waits

- No fixed waits in any suite: in Python, wait for the state (another transaction holding a
  lock, an event received), never a sleep; time-dependent page code runs on `page.clock`;
  screenshots use `animations: "disabled"`. A mocked slow reply is held until the test
  releases it, never delayed by a timer.
- Poll with a timeout or wait on a signal; control the clock rather than waiting it out.

## Test data

- Each test makes its own data (defaults plus the overrides it cares about, fresh uuids) and
  removes it; never rely on rows a developer or another test left.
- Setup and cleanup sit together in a fixture, not spread over hooks or `try/finally` in
  tests; repeated pairs move into a fixture when touched.

## Flaky tests

- Fix a flaky test at the cause; a retry or rerun is a stopgap, and a pass on retry counts as
  flaky. A test that needs quarantine is quarantined briefly, tracked and fixed.
- Each test passes on its own and in any order; no test depends on another's leftovers.
- This applies to every kind of test, everywhere: unit, integration, browser, load, evals and
  scripted end-to-end checks. Unit tests: no module-level state shared between tests (caches such
  as `lru_cache`, settings, singletons, fake stores and mocks reset or recreated per test; fake
  timers and `vi` mocks restored); integration tests: their rows and keys created per test and
  cleaned before and after; load runs and evals: their own throwaway accounts, removed at the end.
- Every test starts absolutely clean: a fresh browser context (no cookies, storage or open
  streams), and its own users, companies, interviews and invites created for it (no shared fixture
  users or data, no `beforeAll` users shared across tests, nothing read that another test made);
  server-side state it can trip (rate-limit counters, open streams, caches) keyed by its own
  identities. Isolation comes from per-test data, never from wiping the shared local databases.
  Cleanup runs before each test as well as after, and a global setup removes leftovers of crashed
  runs.
- A test that fails in the full run but passes alone is an order dependency until proven
  otherwise, never "flaky under load" by default: rerun it after the tests that preceded it and
  in reverse order, find the shared state (data, saved settings on shared users, cookies, caches,
  rate-limit counters keyed by IP or email) and make the test own it.
- The suite never trips the product's own limits: if test traffic hits a limit (the gateway's
  per-IP limit, sign-up or email caps), fix it on the test side (a local-only bypass or isolated
  keys), never by raising the real limit.

## Coverage and CI

- Coverage finds untested code; it is a report (on changed lines at most), never a target or
  a gate. Mutation testing (mutmut, StrykerJS) finds tests that run code without checking it;
  not set up (rule 4), added only on the user's approval.
- CI: the commit build runs the fast unit suites; a second stage runs real databases and
  browsers.

## Contracts between services

- Generated frontend API types are checked for drift (`openapi-typescript … --check`), as
  the assistant's OpenAPI snapshots are; refresh both with the `api-types` skill.
- A fake of another service is checked against the real one now and then (a contract test),
  so the fake doesn't drift from what the service returns.
- Fuzzing the OpenAPI spec (Schemathesis) finds 5xx and schema violations; not set up,
  added only on the user's approval.

## Security

- IDOR: every endpoint that takes an id is tested with another user's or company's id and
  refuses it; aim for a role × endpoint × owner matrix.
- Dependencies are scanned in CI (pip-audit, `pnpm audit`, osv-scanner; `audit.yml`).

## Third-party integrations

- Fakes in unit tests; recorded responses or a self-initialising fake (RESPX, VCR.py) in
  medium tests; the provider's live sandbox for a few large ones only.
- Paddle: sandbox account and keys, the webhook simulator, and signature checks on the raw
  body, including tampered and expired signatures (`.claude/rules/payments.md`, Tests).
- Resend: only `delivered@`, `bounced@` and `complained@resend.dev` (with `+label`), or
  Mailpit locally; never a real address.
- Slack: requests checked by `X-Slack-Signature`; stale requests refused.
- LLMs: scripted fake chat models in unit tests; answer quality is the evals' job (rule 20).

Research (local notes, git-ignored): `internal_docs/best-practices/testing.md`.
