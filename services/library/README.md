# library

The question bank: every test's and template's topics and questions (companies' interviews and
the public templates), question reuse across tests, practice content, the questions'
statistics and quality checks (ratings, reports, flags, revisions and the patterns behind them),
news posts, account deletion and export across the services, and the erasures replayed after a
restore. It keeps all of it in its own database. Users' email settings and accepted terms are the
accounts service's; library's old internal routes for them forward there for one release
(`api/v1/internal_moved.py`), and its old tables (`email_preferences`, `email_consents`,
`terms_acceptances`) go in the next release. What it does and its settings:
[templates and practice](../../docs/features/templates-and-practice.md) and
[the admin zone](../../docs/features/admin-zone.md).

## Layout

```
src/library/
├── main.py, config.py      # App wiring; settings
├── api/v1/                 # Routes (the folder name only: URLs have no extra /v1)
├── api/dependencies.py     # Calls from other services
├── core/                   # db.py (engine, Session), security.py (service tokens)
├── handlers/               # Pub/Sub events (answers, scored topics, deleted guests, fixed
│                           # bank questions, deleted interviews and companies); dispatch.py
│                           # picks one
├── services/               # Sets and templates, quality reviews and fixes, feedback, news,
│                           # account deletion and export, erasures; each opens its
│                           # transaction
├── repositories/           # Database queries: sets, templates, pools, statistics, quality,
│                           # feedback, news, erasures, ...; take the session, never commit
├── models/, schemas/       # SQLAlchemy tables; request and response models
├── helpers/, constants/    # Pure functions (pools, slugs, quality flags); fixed values
├── integrations/           # Other services (account deletion, accounts, generation), Redis
└── jobs/db_roles.py        # `python -m library.jobs.db_roles`: each service's Postgres user
tests/unit/, tests/integration/   # Mirror src/
migrations/                       # Alembic
```

Routes and handlers call services; services open the transaction (`async with
Session.begin() as session:`) and pass it to the repositories, so an action's steps are saved
together, and call generation, the other services, Firebase and Redis outside it. A plain read
may open `async with Session() as session:` in the route. `tests/unit/test_layers.py` checks the
imports and that no repository commits; batched deletions take the session factory, each batch
its own transaction.

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
