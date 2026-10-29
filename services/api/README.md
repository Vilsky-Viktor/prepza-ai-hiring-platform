# api

The public API at `/api/v1/` (companies' API keys, their interviews and candidates, web hooks)
and the API page's management routes, and the count of a company's working keys and web hooks
for its menu (`/internal/companies/{id}/active-count`, companies only). It keeps the keys, web
hooks, deliveries and retries in its
own database; interviews, candidates and invites come from the companies service. What it does
and its settings: [docs/features/api.md](../../docs/features/api.md).

## Layout

```
src/api/
├── main.py, config.py      # App wiring; settings
├── api/v1/                 # Routes (the folder name only: URLs have no extra /v1)
├── api/dependencies.py     # The API key and its permissions, calls from other services
├── core/                   # db.py (engine, Session), exceptions.py, security.py (service tokens)
├── handlers/               # Companies' and accounts' Pub/Sub events, one module per event;
│                           # dispatch.py picks it
├── services/               # Key checks, management, web hook sends and retries, account
│                           # deletions, idempotency; each opens its transaction
├── repositories/           # Database queries: keys, web hooks, deliveries, retries, the log;
│                           # take the session, never commit
├── models/, schemas/       # SQLAlchemy tables; request and response models
├── helpers/, constants/    # Pure functions; fixed values and the API description
└── integrations/           # Companies, Redis, the web hooks' HTTP client
tests/unit/, tests/integration/   # Mirror src/
migrations/                       # Alembic
```

Routes and handlers call services; services open the transaction (`async with
Session.begin() as session:`) and pass it to the repositories, so an action's steps are saved
together (`tests/unit/test_layers.py` checks the imports and that no repository commits).

`src/` is on the path (`PYTHONPATH` in the Dockerfile, `pythonpath` for pytest,
`prepend_sys_path` for Alembic), so the package imports as `api` (`api.api.v1.public`).

## Commands

```bash
docker compose up -d --build api                 # the service and its migrations
cd services/api && uv run pytest                 # unit tests
scripts/integration.sh api                       # integration tests (real Postgres and Redis)
scripts/assistant-openapi.sh                     # refresh the assistant's snapshot of these routes
```
