# notifications

prepza's emails, Slack messages and in-app notices: invites, reminders, reports and contact
messages from other services' events; the members' digest and reminders each morning; legal
notices and campaigns through the bulk sender; the bell's notifications and their live stream;
posts to a company's Slack channel (and whether it's connected, for the company's menu:
`/internal/companies/{id}/active-count`, companies only); unsubscribe links, candidates' opt-outs and the suppression
list fed by Resend's web hooks. It keeps all of it in its own database. What it does and its
settings: [notifications and emails](../../docs/features/notifications.md); the email rules:
`.claude/rules/email.md`.

## Layout

```
src/notifications/
├── main.py, config.py      # App wiring; settings
├── api/v1/                 # Routes (the folder name only: URLs have no extra /v1)
├── api/dependencies.py     # Calls from other services
├── core/                   # db.py (engine, Session), security.py (service tokens)
├── handlers/               # Pub/Sub events (requested notifications, the team's notes, invites, reminders,
│                           # reports, contact messages, Resend's web hooks, campaigns'
│                           # translations, deletions);
│                           # dispatch.py picks one
├── services/               # Sending (Resend, pacing, suppression), the bell, Slack, the
│                           # morning emails, bulk sends, campaigns, legal notices,
│                           # unsubscribes, account and company deletion; each opens its
│                           # transaction
├── repositories/           # Database queries: notifications, sent emails, bulk sends,
│                           # campaigns, opt-outs, suppression, Slack, ...; take the session,
│                           # never commit
├── models/, schemas/       # SQLAlchemy tables; request and response models
├── helpers/, constants/    # Pure functions (emails, unsubscribe links, Slack messages); fixed
│                           # values
├── templates/              # The emails' layout and texts (languages/: one module per language)
└── integrations/           # Resend, SMTP (Mailpit locally), Slack, the other services, Redis
tests/unit/, tests/integration/   # Mirror src/
migrations/                       # Alembic
```

Routes and handlers call services; services open the transaction (`async with
Session.begin() as session:`) and pass it to the repositories, so an action's steps are saved
together, and call Resend, Slack, Redis and the other services outside it. A plain read may open
`async with Session() as session:` in the route. `tests/unit/test_layers.py` checks the imports
and that no repository commits; batched deletions and the skipping of a stopped send's
recipients take the session factory, each batch its own transaction.

`src/` is on the path (`PYTHONPATH` in the Dockerfile, `pythonpath` for pytest,
`prepend_sys_path` for Alembic), so the package imports as `notifications`
(`notifications.api.v1.me`).

## Commands

```bash
docker compose up -d --build notifications       # the service and its migrations
cd services/notifications && uv run pytest       # unit tests
scripts/integration.sh notifications             # integration tests (real Postgres and Redis)
scripts/assistant-openapi.sh                     # refresh the assistant's snapshot of these routes
```
