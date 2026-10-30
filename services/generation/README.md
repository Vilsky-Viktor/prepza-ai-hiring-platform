# generation

The AI pipeline: it reads a job posting (or a template's brief), drafts the test's topics for a
member to review, writes each topic's questions and options, checks the answer keys, and saves
the result to library. It also re-generates single questions, adds questions to templates,
verifies questions flagged by users, tags code examples, translates news and campaigns,
finds the patterns behind flagged questions, and filters companies' proven questions before they
join the shared question bank. Each AI call is capped, traced and priced, and a
company's or the platform's AI spend limit stops new work. Its own database keeps the runs, the
graph's checkpoints, the batched work and the quality patterns. What it does and its settings:
[Generation and question quality](../../docs/generation.md).

Two apps share the code: `main.py` (the API other services and the admin zone call) and
`worker_main.py` (the worker: Cloud Tasks runs the jobs and Cloud Scheduler the schedules
through it; it holds the LangGraph graph and its checkpointer).

## Layout

```
src/generation/
├── main.py, worker_main.py # The API's and the worker's wiring
├── config.py               # Settings
├── api/v1/                 # Routes (the folder name only: URLs have no extra /v1); jobs.py and
│                           # schedules.py are the worker's
├── api/dependencies.py     # Calls from other services
├── core/                   # db.py (engine, Session), security.py (service tokens)
├── handlers/               # Pub/Sub events (accounts' `user.deleted`), pushed to the API;
│                           # dispatch.py picks one
├── services/               # The pipeline, its jobs, re-generation, the verifier, additions,
│                           # budgets, batches, translations, patterns, schedules
├── services/nodes/         # The graph's nodes, one per module
├── repositories/           # Database queries: generations, batched work, key checks,
│                           # patterns, account data; the checkpointer; the draft cache (Redis)
├── models/, schemas/       # SQLAlchemy tables; request, response and model-output schemas
├── prompts/                # The model prompts, one module per task
├── helpers/, constants/    # Pure functions (payloads, progress, questions); fixed values
├── integrations/           # library, Cloud Tasks, OpenAI (chat, batch), Redis,
│                           # AI usage
└── jobs/                   # One-off and maintenance runs (`python -m generation.jobs.<name>`)
tests/unit/, tests/integration/   # Mirror src/
migrations/                       # Alembic (and LangGraph's checkpoint tables)
```

Routes call services; services open the transaction (`async with Session.begin() as
session:`) and pass it to the repositories, and call the model, library, notifications, Cloud
Tasks and Redis outside it: a run's row is saved between model calls, a start is saved before
its job is queued, and what the weekly pattern job found is saved in one transaction after its
call. A plain read may open `async with Session() as session:` in the route.
`tests/unit/test_layers.py` checks the imports and that no repository commits; clearing old
pasted texts takes a transaction per batch.

`src/` is on the path (`PYTHONPATH` in the Dockerfile, `pythonpath` for pytest,
`prepend_sys_path` for Alembic, `evals/run.sh` and `scripts/graph-diagrams.sh`), so the package
imports as `generation` (`generation.api.v1.internal`). The worker's command names
`generation.worker_main:app` in compose and in Terraform (`infra/terraform/locals.tf`). The
offline evals (`evals/`) import this code and hash `src/generation/prompts/`.

## Commands

```bash
docker compose up -d --build generation generation-worker   # the API, the worker, migrations
cd services/generation && uv run pytest                     # unit tests
scripts/integration.sh generation                           # integration tests (real Postgres, Redis)
scripts/graph-diagrams.sh                                   # redraw the graph in docs/generation.md
scripts/assistant-openapi.sh                                # refresh the assistant's snapshot
docker compose exec generation uv run --no-sync python -m generation.jobs.embed_templates
```
