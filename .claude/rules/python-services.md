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
