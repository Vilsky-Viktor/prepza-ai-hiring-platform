# library

The question bank: every test's and template's topics and questions (companies' interviews and
the public templates), question reuse across tests, practice content, the questions'
statistics and quality checks (ratings, reports, flags, revisions and the patterns behind them),
news posts, users' email settings and accepted terms, account deletion and data export across
the services, and the erasures replayed after a restore. It keeps all of it in its own database.
What it does and its settings: [templates and practice](../../docs/features/templates-and-practice.md),
[the admin zone](../../docs/features/admin-zone.md) and
[notifications](../../docs/features/notifications.md) (email settings).

## Layout

```
src/library/
├── main.py, config.py      # App wiring; settings
├── api/v1/                 # Routes (the folder name only: URLs have no extra /v1)
├── api/dependencies.py     # Calls from other services
├── core/                   # db.py (engine, Session), security.py (service tokens)
├── handlers/               # Pub/Sub events (answers, scored topics, deleted guests, fixed
│                           # bank questions); dispatch.py picks one
├── services/               # Quality reviews, account deletion and export, erasures, news,
│                           # copy fixes, set saves
├── repositories/           # Database queries: sets, templates, pools, statistics, quality,
│                           # feedback, email settings, news, erasures, ...
├── models/, schemas/       # SQLAlchemy tables; request and response models
├── helpers/, constants/    # Pure functions (pools, slugs, quality flags); fixed values
├── integrations/           # Other services (account deletion, billing, generation), Redis
└── jobs/db_roles.py        # `python -m library.jobs.db_roles`: each service's Postgres user
tests/unit/, tests/integration/   # Mirror src/
migrations/                       # Alembic
```

`src/` is on the path (`PYTHONPATH` in the Dockerfile, `pythonpath` for pytest,
`prepend_sys_path` for Alembic, `evals/run.sh`), so the package imports as `library`
(`library.api.v1.internal`). The signed-in browser tests' seed
(`e2e_tests/signed-in/seed/template.py`) runs in this service's container.

## Commands

```bash
docker compose up -d --build library             # the service and its migrations
cd services/library && uv run pytest             # unit tests
scripts/integration.sh library                   # integration tests (real Postgres and Redis)
scripts/assistant-openapi.sh                     # refresh the assistant's snapshot of these routes
```
