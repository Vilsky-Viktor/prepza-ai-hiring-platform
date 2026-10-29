# companies

Companies and who may do what in them: companies, members, roles and their invites, the
access checks every company route runs, interviews (tests) and their settings, candidates and
their invites (one by one, from lists, through a shareable link, from an ATS or the public
API), results and reports, the company's brand (logo, colors, style), domain verification, AI
app and integration settings, the action log, and the admin zone's company pages and support
search. Credits are held and charged through billing. It keeps all of it in its own database.
What it does and its settings: [companies](../../docs/features/companies.md),
[interviews](../../docs/features/interviews.md), [candidates](../../docs/features/candidates.md),
[the admin zone](../../docs/features/admin-zone.md) and
[support](../../docs/features/admin-support.md).

## Layout

```
src/companies/
├── main.py, config.py      # App wiring; settings
├── api/v1/                 # Routes (the folder name only: URLs have no extra /v1)
├── api/dependencies.py     # Calls from other services; what a request came through (Via)
├── core/                   # db.py (engine, Session), security.py (service tokens, the
│                           # X-Assistant header's claims), exceptions.py
├── handlers/               # Pub/Sub events (finished interviews, generation outcomes, other
│                           # services' actions for the log); dispatch.py picks one
├── services/               # Access checks, invites, links, credits, results, reports,
│                           # account and company deletion, the action log; each opens its
│                           # transaction
├── repositories/           # Database queries: companies, members, interviews, invites,
│                           # candidates, the action log, ...; take the session, never commit
├── models/, schemas/       # SQLAlchemy tables; request and response models
├── helpers/, constants/    # Pure functions (lists, brand colors, notifications); fixed values
└── integrations/           # accounts, billing, generation, library, rounds, Firebase, Redis
tests/unit/, tests/integration/   # Mirror src/
migrations/                       # Alembic
```

Every route that reaches a company's data resolves it and checks the caller's role on it
(`services/access.py`); `tests/unit/test_route_guards.py` fails on a route without a guard, and
`tests/integration/api/test_access_matrix.py` on one that lets another company, a viewer's change
or anyone signed out through.

Routes and handlers call services; services open the transaction (`async with
Session.begin() as session:`) and pass it to the repositories, so a change and its line in the
action log, its email or its notification are saved together, and call billing, generation,
library, rounds and Redis outside it. A plain read may open `async with Session() as session:`
in the route. `tests/unit/test_layers.py` checks the imports and that no repository commits;
batched deletions (a company's or an interview's invites, interviews and action log) take a
transaction per batch.

`src/` is on the path (`PYTHONPATH` in the Dockerfile, `pythonpath` for pytest,
`prepend_sys_path` for Alembic), so the package imports as `companies`
(`companies.api.v1.members`).

## Commands

```bash
docker compose up -d --build companies           # the service and its migrations
cd services/companies && uv run pytest           # unit tests
scripts/integration.sh companies                 # integration tests (real Postgres and Redis)
scripts/assistant-openapi.sh                     # refresh the assistant's snapshot of these routes
python -m companies.services.round_companies     # one-off backfill (in the container)
```
