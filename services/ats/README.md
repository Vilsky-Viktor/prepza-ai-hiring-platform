# ats

Companies' ATS connections (Workable, Greenhouse, Teamtailor, Recruitee, Breezy): the jobs
linked to interviews, the candidates each ATS sends (invited through companies) and the results
written back when they finish; companies asks it how many connections work, for the company's
menu (`/internal/companies/{id}/active-count`). It keeps connections, linked jobs and candidates in its own
database. What it does and its settings: [docs/features/ats.md](../../docs/features/ats.md).

## Layout

```
src/ats/
├── main.py, config.py      # App wiring; settings
├── api/v1/                 # Routes (the folder name only: URLs have no extra /v1)
├── api/dependencies.py     # Calls from other services
├── core/                   # db.py (engine, Session), security.py (service tokens)
├── handlers/               # Pub/Sub events, one module per event; dispatch.py picks it
├── services/               # Connecting, linking jobs, inviting candidates, reporting results,
│                           # the recovery job, the ATSs' web hooks, account deletions; each
│                           # opens its transaction
├── repositories/           # Database queries: connections, links, candidates, kept results;
│                           # take the session, never commit
├── models/, schemas/       # SQLAlchemy tables; request and response models
├── helpers/, constants/    # Pure functions; fixed values
├── integrations/           # One client per ATS, companies, Redis
└── templates/              # The comment written in the ATS, one module per language
tests/unit/, tests/integration/   # Mirror src/
migrations/                       # Alembic
```

Routes and handlers call services; services open the transaction (`async with
Session.begin() as session:`) and pass it to the repositories, so an action's steps are saved
together, and call the ATSs and companies outside it (`tests/unit/test_layers.py` checks the
imports and that no repository commits). Batched deletes and requeues take the session factory,
each batch its own transaction.

`src/` is on the path (`PYTHONPATH` in the Dockerfile, `pythonpath` for pytest,
`prepend_sys_path` for Alembic), so the package imports as `ats` (`ats.api.v1.ats_connect`).

## Commands

```bash
docker compose up -d --build ats                 # the service and its migrations
cd services/ats && uv run pytest                 # unit tests
scripts/integration.sh ats                       # integration tests (real Postgres and Redis)
scripts/assistant-openapi.sh                     # refresh the assistant's snapshot of these routes
```
