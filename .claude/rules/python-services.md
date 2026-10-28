---
paths:
  - "services/**"
  - "packages/**"
---

# Python services

## Layout

Every Python service follows this layout (rule 3's one kind per module still holds):

```
my_service/
├── pyproject.toml, README.md   # the repo's .env.example, .gitignore and scripts cover the rest
├── src/my_service/
│   ├── main.py, config.py   # App setup only (no route logic); Pydantic Settings
│   ├── api/v1/, api/dependencies.py   # Routes; current user, sessions, auth
│   ├── core/                # Exceptions, security, logging
│   ├── models/, schemas/    # SQLAlchemy models; Pydantic request/response models
│   ├── repositories/        # Every database query; take a session, never commit
│   └── services/            # Business logic; owns the transaction
├── tests/unit/, tests/integration/, tests/conftest.py   # Mirrors src/
└── migrations/              # Alembic
```

The engine and sessions are in `core/db.py`; the Pub/Sub event handling is in `handlers/` (one
module per event, `dispatch.py` picks it); `helpers/`, `constants/`, `prompts/`, `integrations/`
and `jobs/` are their own folders in the package.

## Routes, services, repositories

- **Routes** (`api/v1/`) do HTTP only: input, auth and access through dependencies, one call,
  the response model and status. A route with a rule, more than one write or an event calls a
  service; a plain read may open `async with Session() as session:` and call one repository
  function directly (no forwarding services).
- **Services** hold the rules and own the transaction: `async with Session.begin() as session:`
  (the `AsyncSession` is the unit of work), passed to each repository call. Each action is a
  single save: steps that must succeed together share one transaction; calls to other services
  or models happen outside it.
- **Repositories** are module functions taking `session: AsyncSession` first: queries, writes
  and locks (`FOR UPDATE`, `ON CONFLICT`), returning models. No commit, no decisions; pure
  calculations come from `helpers/`. The one exception is batched work, each batch its own
  transaction (`prepza_common.db.db.delete_in_batches` takes the session factory; scalability.md).
- Imports go one way: `api` → `services` → `repositories` → `models`; `helpers`, `constants`
  and `schemas` from anywhere.
- Never commit in a `yield` dependency: its exit runs after the response.
- Not adopted (rule 4): repository classes, a generic base repository, a unit-of-work class,
  domain models apart from the ORM, domain exceptions mapped to HTTP (every entry point is an
  HTTP route, so services may raise `HTTPException`).

## Event-driven services

A worker (Pub/Sub, outbox, scheduled jobs, task queues) is packaged as in the layout above with
`src/<service>/` holding `main.py` (starts the subscribers or loop), `config.py`, `domain/`
(entities and exceptions, free of the framework), `events/` (`schemas.py` for incoming and
outgoing events, `mapping.py` to domain models), `handlers/` (one module per event) and
`infrastructure/` (broker, database session, external clients). A service that also serves HTTP
keeps the layout above and adds `events/` and `handlers/` beside `api/`. Every handler is
idempotent, safe to retry and independent of event order (rule 11); a handler is an entry point
like a route and calls services, never repositories with their own commit.

## Shared library

`packages/common` (`prepza_common`) holds only what two or more services use (rule 10). Services
install it as an editable path dependency from the same commit: no releases, no version pins.

- Layout: `src/prepza_common/` with `py.typed` and modules grouped by area (`ai/`, `auth/`,
  `db/`, `events/`, `http/`, `i18n/`, `limits/`, and `config/` for the shared constants and
  settings base, `observability/` for logs, Sentry and scrubbing, `redis/` for the Redis client,
  lock and the per-instance cache), one concern per module; `tests/unit/` mirrors it (repo-wide
  checks stay at its top); the README names each module in one line, under its area.
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
  (`prepza_common.http.http`). Retry only idempotent calls, at one layer only, with exponential
  backoff and jitter and a cap on attempts; never two back-to-back retries. A side-effecting
  call carries an idempotency key.
- Deadlines, overload answers and scaling limits: `.claude/rules/scalability.md`.
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
  health check (`prepza_common.redis.redis_client`). The service keeps working, degraded, while Redis
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

Research (local notes, git-ignored): `internal_docs/best-practices/architecture.md`,
`internal_docs/best-practices/controller-service-repository.md`.
