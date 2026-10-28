---
name: api-types
description: Refresh the assistant's API snapshots and the frontend's generated API types after a service's routes or schemas change.
---

# Refresh API snapshots and frontend types

A change to a service's routes or schemas must reach two generated copies in the same commit:

- the assistant's snapshots, `services/assistant/src/assistant/openapi/<service>.json`, which its
  tools are built from;
- the frontend's types, `frontend/src/types/api/<service>.ts` (accounts, ats, billing, companies,
  generation, library, notifications, rounds).

The local stack must be running with the change loaded (the services reload on save).

## Steps

```bash
scripts/assistant-openapi.sh

cd frontend
pnpm api-types   # every service's types from the gateway, then prettier over types/api
pnpm typecheck
```

CI's stack job runs both scripts and fails when a snapshot or a type file differs from what
the code generates.

## Check

- `git diff --stat frontend/src/types/api services/assistant/src/assistant/openapi`: only what the
  change explains. A larger diff means an earlier change was never refreshed; keep it, and say so.
- `cd services/assistant && uv run pytest -q tests/unit` still passes.
- If a URL answers 500 or times out, it may be the frontend answering an unknown path: check the
  gateway's route in `gateway/nginx.conf` before suspecting the service.
