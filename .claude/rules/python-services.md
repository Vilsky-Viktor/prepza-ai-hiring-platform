---
paths:
  - "services/**"
  - "packages/**"
---

# Python services

## Layout

Every Python service follows this layout (it replaces the `app/` layout; rule 3's one kind per
module still holds):

```
my_service/
├── pyproject.toml, README.md, Makefile, .env.example, .gitignore
├── src/my_service/
│   ├── main.py, config.py   # App setup only (no route logic); Pydantic Settings
│   ├── api/v1/, api/dependencies.py   # Routes; current user, sessions, auth
│   ├── core/                # Exceptions, security, logging
│   ├── models/, schemas/    # SQLAlchemy models; Pydantic request/response models
│   ├── repositories/        # Every database query
│   └── services/            # Business logic
├── tests/unit/, tests/integration/, tests/conftest.py   # Mirrors src/
└── migrations/              # Alembic
```

From today's layout: `routers/` → `api/v1/`, `storage/` → `repositories/`, `auth.py` and
`service_auth.py` → `api/dependencies.py` and `core/`; `helpers/`, `constants/`, `prompts/` and
`integrations/` stay their own folders in the package.

## Event-driven services

A worker (Pub/Sub, outbox, scheduled jobs, task queues) is packaged as in the layout above with
`src/<service>/` holding `main.py` (starts the subscribers or loop), `config.py`, `domain/`
(entities and exceptions, free of the framework), `events/` (`schemas.py` for incoming and
outgoing events, `mapping.py` to domain models), `handlers/` (one module per event) and
`infrastructure/` (broker, database session, external clients). A service that also serves HTTP
keeps the layout above and adds `events/` and `handlers/` beside `api/`. Every handler is
idempotent, safe to retry and independent of event order (rule 11).

## Shared library

`packages/common` (`prepza_common`) holds only what two or more services use (rule 10). Services
install it as an editable path dependency from the same commit: no releases, no version pins.

- Layout: `src/prepza_common/` with `py.typed` and modules grouped by area (`ai/`, `auth/`,
  `db/`, `events/`, `http/`, `i18n/`, `limits/`), one concern per module; `tests/unit/` mirrors
  it; the README names each module in one line.
- Generic only: no routes, tables, prompts or decisions of one service; what differs comes in
  as arguments. A dependency only some services need is an optional extra.
- Import from the module itself; `__init__.py` re-exports nothing.
- A change updates every caller in the same commit and runs the library's tests and every
  user's unit tests; nothing deprecated is kept. Moving code in deletes the services' copies and
  moves their tests.

## Calls between services

- Synchronous HTTP only where the caller needs the answer now; everything that can happen later
  goes through events: the event row is written in the same transaction as the change (outbox),
  published only once committed, and every consumer is idempotent on the event's id (delivery is
  at least once; rule 11).
- Every call has a timeout set from the callee's latency, through the shared client
  (`prepza_common.http`). Retry only idempotent calls, at one layer only, with exponential
  backoff and jitter and a cap on attempts; never two back-to-back retries. A side-effecting
  call carries an idempotency key.
- No circuit breakers or extra resilience layers (rule 4): Pub/Sub and Cloud Tasks retry with
  backoff and dead-letter, and synchronous calls have timeouts.
- Calls to other services carry the request's `X-Cloud-Trace-Context`, so one user action can
  be followed across services in the logs.

## FastAPI on Cloud Run

- Start-up and shutdown in the lifespan (never `on_event`). `async def` only around awaitable
  IO; blocking work (a sync SDK, image decoding, CPU-heavy code) runs in `asyncio.to_thread`.
- One Uvicorn process per container, exec-form `CMD`, `--timeout-graceful-shutdown` under Cloud
  Run's 10 s between SIGTERM and SIGKILL (5–8 s), so in-flight requests and Sentry's flush end
  in time.
- No work after the response: request-based billing throttles the CPU once the response is
  sent, so background tasks stall or are lost. Await the work (with a short timeout) or hand it
  to an event.
- `/health` checks only the process (liveness: never a dependency, or a database outage restarts
  every instance); `/ready` checks the database and is the startup probe.

## Redis

- Connect and command timeouts, retries with backoff and jitter on connection errors and a
  health check (`prepza_common.redis_client`). The service keeps working, degraded, while Redis
  is down: limits keep their last values, switches their last state.
- Test fakes for Redis or other shared clients live once beside the shared library's tests and
  are imported by services, never copied (rule 10).

## Logs and errors

- One-line JSON logs with the fields Cloud Logging reads: `severity`, `message`, `time`,
  `logging.googleapis.com/trace`. Every logger in the process writes that format, Uvicorn's
  included; no plain-text access log (Cloud Run's request log already records each request).
- Log ids, never emails, names, tokens or other personal data; a URL path that carries a token
  is logged as its route template (`.claude/rules/security.md`).
- Sentry: `send_default_pii=False`, no local variables, users by internal id.

Research (local notes, git-ignored): `internal_docs/architecture-best-practices.md`.
