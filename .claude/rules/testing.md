---
paths:
  - "**/tests/**"
  - "e2e_tests/**"
---

# Tests

What a test checks and where it lives is rule 8; these are the mechanics.

## Browser, load and smoke tests

`e2e_tests/`: `pages/` (signed out), `signed-in/` (Auth emulator, `fixtures.ts`, `teardown.ts`),
`load/` (k6, never against production), `smoke.sh` (read-only, any environment), `flow.py` and
`mcp.py`; each suite runs in its Docker image through its script.

- One spec per screen or flow, named after it. Signed-in specs run in one worker in letter
  order, and each passes on its own.
- Tests own their data through fixtures and teardown (setup and cleanup together in a fixture,
  not in hooks); each test makes its own rows; repeated steps in `helpers/` (one module per
  area); no page objects (rule 4).
- Locators as rule 8; web-first assertions (`await expect(locator)...`); no fixed waits
  (`waitForTimeout`): wait for an element, a response or a state. Every promise is awaited.
- At most one retry; a test that needs it is fixed. Traces kept on failure. Load scenarios have
  k6 thresholds and delete what they made.

Research (local notes, git-ignored): `internal_docs/best-practices-sources.md`.
