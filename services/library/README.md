# library

The question bank: every test's and template's topics and questions (companies' interviews and
the public templates), question reuse across tests, the shared question bank of companies'
proven questions (which outlives the company that wrote them), practice content, the questions'
statistics (with each question's difficulty, for rounds' answer patterns) and quality checks (ratings, reports, flags, revisions and the patterns behind them).
It keeps all of it in its own database. Users' accounts (email settings, accepted
terms, deleting and downloading an account, the erasures replayed after a restore) are the
accounts service's: library deletes a user's votes and reports on its `user.deleted` event and
exports them when it asks (`/internal/users/{id}/export`); news posts are the site service's. What it does and its settings:
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
│                           # bank questions, deleted interviews, companies and accounts,
│                           # interviews kept out of the shared bank);
│                           # dispatch.py picks one
├── services/               # Sets and templates, quality reviews and fixes, feedback, a
│                           # user's votes and reports; each opens its transaction
├── repositories/           # Database queries: sets, templates, pools, statistics, quality,
│                           # feedback, ...; take the session, never commit
├── models/, schemas/       # SQLAlchemy tables; request and response models
├── helpers/, constants/    # Pure functions (pools, slugs, quality flags); fixed values
└── integrations/           # Other services (generation), Redis
tests/unit/, tests/integration/   # Mirror src/
migrations/                       # Alembic
```

Routes and handlers call services; services open the transaction (`async with
Session.begin() as session:`) and pass it to the repositories, so an action's steps are saved
together, and call generation and Redis outside it. A plain read
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
