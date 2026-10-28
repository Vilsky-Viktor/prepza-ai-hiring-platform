# notifications

prepza's emails, Slack messages and in-app notices: invites, reminders, reports and contact
messages from other services' events; the members' digest and reminders each morning; legal
notices and campaigns through the bulk sender; the bell's notifications and their live stream;
posts to a company's Slack channel; unsubscribe links, candidates' opt-outs and the suppression
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
├── handlers/               # Pub/Sub events (requested notifications, invites, reminders,
│                           # reports, contact messages, Resend's web hooks, deletions);
│                           # dispatch.py picks one
├── services/               # Sending (Resend, pacing, suppression), the bell, Slack, the
│                           # morning emails, bulk sends, campaigns, legal notices, unsubscribes
├── repositories/           # Database queries: notifications, sent emails, bulk sends,
│                           # campaigns, opt-outs, suppression, Slack, ...
├── models/, schemas/       # SQLAlchemy tables; request and response models
├── helpers/, constants/    # Pure functions (emails, unsubscribe links, Slack messages); fixed
│                           # values
├── templates/              # The emails' layout and texts (languages/: one module per language)
└── integrations/           # Resend, SMTP (Mailpit locally), Slack, the other services, Redis
tests/unit/, tests/integration/   # Mirror src/
migrations/                       # Alembic
```

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
