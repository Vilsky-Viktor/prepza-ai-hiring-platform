# accounts

Users' accounts: the account settings (the interface language, kept on the Firebase sign-in),
users' email settings with their consent log, the terms each accepted at sign-up, the admin
zone's account lookups, email settings and sign-up stats, and what other services ask about an
account (its address, language and email settings, account ids, when it was made). It keeps the
email settings, the consent log and the accepted terms in its own database; the sign-ins are
Firebase's. What it does: [notifications](../../docs/features/notifications.md#email-preferences-and-consent)
(email settings), [the public site](../../docs/features/site.md) (accepted terms) and
[support](../../docs/features/admin-support.md).

Its public routes keep the addresses library had: the gateway (`gateway/nginx.conf`) and the
load balancer (`locals.account_paths`) send `/api/library/me/settings`,
`/api/library/me/email-preferences`, `/api/library/superadmin/emails/...` and
`/api/library/superadmin/stats` here, so the frontend's calls didn't change. It's also at
`/api/accounts/` (its API description, for the frontend's types).

## Layout

```
src/accounts/
├── main.py, config.py      # App wiring; settings
├── api/v1/                 # Routes (the folder name only: URLs have no extra /v1)
├── api/dependencies.py     # Calls from other services
├── core/                   # db.py (engine, Session), security.py (service tokens)
├── handlers/               # Pub/Sub events (deleted guests); dispatch.py picks one
├── services/               # Sign-ins and language, email settings, recipients, stats, an
│                           # account's data, deleted guests; each opens its transaction
├── repositories/           # Database queries: email settings and consents, terms, an
│                           # account's data; take the session, never commit
├── models/, schemas/       # SQLAlchemy tables; request and response models
├── helpers/, constants/    # Pure functions (consent changes); fixed values
├── integrations/           # billing (a new account's currency), Redis
└── jobs/copy_from_library.py   # one-off: library's rows of these tables copied here
tests/unit/, tests/integration/   # Mirror src/
migrations/                       # Alembic
```

Routes and handlers call services; services open the transaction (`async with
Session.begin() as session:`) and pass it to the repositories, so an action's steps are saved
together, and call Firebase and billing outside it (`tests/unit/test_layers.py` checks the
imports and that no repository commits).

`src/` is on the path (`PYTHONPATH` in the Dockerfile, `pythonpath` for pytest,
`prepend_sys_path` for Alembic), so the package imports as `accounts` (`accounts.api.v1.me`).

## Copying library's rows

Library held these tables before this service. `accounts.jobs.copy_from_library` copies its
rows here, safe to repeat (a row already here is kept as it is); it was run locally, and
production had none before launch:

```bash
docker compose exec -e LIBRARY_DATABASE_URL=postgresql://library:<password>@postgres:5432/library \
  accounts python -m accounts.jobs.copy_from_library
```

## Commands

```bash
docker compose up -d --build accounts            # the service and its migrations
cd services/accounts && uv run pytest            # unit tests
scripts/integration.sh accounts                  # integration tests (real Postgres and Redis)
scripts/assistant-openapi.sh                     # refresh the assistant's snapshot of these routes
```
