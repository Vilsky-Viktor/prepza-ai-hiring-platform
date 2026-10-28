# accounts

Users' accounts. It keeps what it holds in its own database.

## Layout

```
src/accounts/
├── main.py, config.py      # App wiring; settings
├── api/v1/                 # Routes (the folder name only: URLs have no extra /v1)
├── api/dependencies.py     # Calls from other services
├── core/                   # db.py (engine, Session), security.py (service tokens)
├── handlers/               # Pub/Sub events, one module per event; dispatch.py picks it
├── models/                 # SQLAlchemy tables
├── constants/              # Fixed values
└── integrations/           # Redis
tests/unit/, tests/integration/   # Mirror src/
migrations/                       # Alembic
```

`src/` is on the path (`PYTHONPATH` in the Dockerfile, `pythonpath` for pytest,
`prepend_sys_path` for Alembic), so the package imports as `accounts`
(`accounts.api.v1.internal_events`).

## Commands

```bash
docker compose up -d --build accounts            # the service and its migrations
cd services/accounts && uv run pytest            # unit tests
scripts/integration.sh accounts                  # integration tests (real Postgres and Redis)
```
