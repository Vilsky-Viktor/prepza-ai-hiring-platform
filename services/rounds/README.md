# rounds

Candidates' interview sessions and their answers, and free practice rounds. It keeps sessions, answers and integrity signals in its own database; questions come from library, and scores go out as
events; a deleted interview's or company's sessions go when its `interview.deleted` or
`company.deleted` arrives. What it does and its settings:
[candidates](../../docs/features/candidates.md) and
[templates and practice](../../docs/features/templates-and-practice.md).

## Layout

```
src/rounds/
├── main.py, config.py      # App wiring; settings
├── api/v1/                 # Routes (the folder name only: URLs have no extra /v1)
├── api/dependencies.py     # Calls from other services
├── core/                   # db.py (engine, Session), security.py (service tokens)
├── handlers/               # Pub/Sub events (deleted interviews and companies); dispatch.py
│                           # picks one
├── services/               # Interview steps, answers, timed sessions, practice, signals,
│                           # deletions; each opens its
│                           # transaction
├── repositories/           # Database queries (sessions, answers, signals, ...);
│                           # take the session, never commit
├── models/, schemas/       # SQLAlchemy tables; request and response models
├── helpers/, constants/    # Pure functions (scores, exports); fixed values
└── integrations/           # library, Redis
tests/unit/, tests/integration/   # Mirror src/
migrations/                       # Alembic
```

The FAQ, page guides, guide articles, legal texts and the contact form are the site service's
(`/api/site/help/...`); the help chat is the assistant's.

Routes call services; services open the transaction (`async with Session.begin() as
session:`) and pass it to the repositories, so an action's steps are saved together (an
answer with the finish it brings, a step's finished sections with the next question's clock),
and read limits from Redis or call library outside it. A plain read may open
`async with Session() as session:` in the route. `tests/unit/test_layers.py` checks the imports
and that no repository commits; batched deletions take the session factory, each batch its own
transaction.

`src/` is on the path (`PYTHONPATH` in the Dockerfile, `pythonpath` for pytest,
`prepend_sys_path` for Alembic, `evals/run.sh`), so the package imports as `rounds`
(`rounds.api.v1.sessions`).

## Commands

```bash
docker compose up -d --build rounds              # the service and its migrations
cd services/rounds && uv run pytest              # unit tests
scripts/integration.sh rounds                    # integration tests (real Postgres and Redis)
scripts/assistant-openapi.sh                     # refresh the assistant's snapshot of these routes
```
