# accounts

Users' accounts: the account settings (the interface language, kept on the Firebase sign-in),
users' email settings with their consent log, the terms each accepted at sign-up, deleting and
downloading an account across every service, the erasures replayed after a restore, the admin
zone's account lookups, email settings and sign-up stats, and what other services ask about an
account (its address, language and email settings, account ids, when it was made). It keeps the
email settings, the consent log, the accepted terms and the recent erasures in its own database;
the sign-ins are Firebase's. What it does: [notifications](../../docs/features/notifications.md#email-preferences-and-consent)
(email settings), [the public site](../../docs/features/site.md) (accepted terms) and
[support](../../docs/features/admin-support.md).

Its public routes are under `/api/accounts/` (`/api/accounts/me`, the admin zone's
`/api/accounts/superadmin/emails/...` and `/api/accounts/superadmin/stats`).

## Deleting and downloading an account

`DELETE /me` asks companies first (it refuses, 409, while the user owns a company others joined,
before anything is deleted), then every other service at once (rounds, generation, billing,
notifications, ats, api, assistant, library, site: `DELETE /internal/users/{id}`, the verified email in
the body), then deletes its own rows with a note in `erasures` in one save, and the sign-in last,
so a failed step leaves the user able to retry; every step is safe to repeat. `GET /me/export`
asks every service (`POST /internal/users/{id}/export`) and adds its own part. The daily
`erasures` job (`/internal/schedules/erasures`; by hand after a restore) runs the last 14 days'
deletions again everywhere.

## Layout

```
src/accounts/
├── main.py, config.py      # App wiring; settings
├── api/v1/                 # Routes (the folder name only: URLs have no extra /v1)
├── api/dependencies.py     # Calls from other services
├── core/                   # db.py (engine, Session), security.py (service tokens)
├── handlers/               # Pub/Sub events (deleted guests); dispatch.py picks one
├── services/               # Sign-ins and language, email settings, recipients, stats,
│                           # deletion and export, erasures, deleted guests; each opens its
│                           # transaction
├── repositories/           # Database queries: email settings and consents, terms, erasures,
│                           # an account's data; take the session, never commit
├── models/, schemas/       # SQLAlchemy tables; request and response models
├── helpers/, constants/    # Pure functions (consent changes); fixed values
├── integrations/           # Every service's account routes, billing (a new account's
│                           # currency), Redis
└── jobs/copy_from_library.py   # one-off: library's rows of these tables copied here
tests/unit/, tests/integration/   # Mirror src/
migrations/                       # Alembic
```

Routes and handlers call services; services open the transaction (`async with
Session.begin() as session:`) and pass it to the repositories, so an action's steps are saved
together, and call Firebase and the other services outside it (`tests/unit/test_layers.py` checks the
imports and that no repository commits).

`src/` is on the path (`PYTHONPATH` in the Dockerfile, `pythonpath` for pytest,
`prepend_sys_path` for Alembic), so the package imports as `accounts` (`accounts.api.v1.me`).

## Copying library's rows

Library held these tables (`email_preferences`, `email_consents`, `terms_acceptances`,
`erasures`) before this service. `accounts.jobs.copy_from_library` copies its rows here, safe to repeat (a row already here is kept as it is); it was run locally, and
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
