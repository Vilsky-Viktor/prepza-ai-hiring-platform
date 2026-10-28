# billing

Credits and payments: each company's wallet and its append-only ledger, holds on candidates'
credits, top-ups through Paddle (checkouts, Paddle's web hooks, the daily reconciliation),
automatic top-ups, refunds, the welcome gift and referral rewards, currencies and prices; also
every AI call and limit hit the services record (the AI costs tab) and the limits superadmins
edit in Controls. It keeps all of it in its own database. What it does and its settings:
[docs/features/billing.md](../../docs/features/billing.md); the rules for money and Paddle:
`.claude/rules/payments.md`.

## Layout

```
src/billing/
├── main.py, config.py      # App wiring; settings (refuses a sandbox/live mix of Paddle keys)
├── api/v1/                 # Routes (the folder name only: URLs have no extra /v1)
├── api/dependencies.py     # Calls from other services; the visitor's country
├── core/                   # db.py (engine, Session), security.py (service tokens)
├── handlers/               # Pub/Sub events (AI calls, limit hits); dispatch.py picks one
├── services/               # Holds, top-ups, Paddle's web hooks, refunds, automatic top-ups,
│                           # reconciliation, referrals, currencies, account deletions, AI
│                           # costs, limits; each opens its transaction
├── repositories/           # Database queries: ledger, purchases, automatic top-ups, usage, ...;
│                           # take the session, never commit
├── models/, schemas/       # SQLAlchemy tables; request and response models
├── helpers/, constants/    # Pure functions (prices, gift keys, signatures); fixed values
└── integrations/           # Paddle, companies' names, Redis
tests/unit/, tests/integration/   # Mirror src/
migrations/                       # Alembic
```

Routes and handlers call services; services open the transaction (`async with
Session.begin() as session:`) and pass it to the repositories, so an action's steps are saved
together, and call Paddle, companies and Redis outside it (`tests/unit/test_layers.py` checks the
imports and that no repository commits). Batched deletes take the session factory, each batch
its own transaction.

`src/` is on the path (`PYTHONPATH` in the Dockerfile, `pythonpath` for pytest,
`prepend_sys_path` for Alembic), so the package imports as `billing`
(`billing.api.v1.internal`).

## Commands

```bash
docker compose up -d --build billing             # the service and its migrations
cd services/billing && uv run pytest             # unit tests
scripts/integration.sh billing                   # integration tests (real Postgres and Redis)
scripts/assistant-openapi.sh                     # refresh the assistant's snapshot of these routes
```
