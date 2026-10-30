# site

The public site's content: the FAQ, each page's guide, the guide articles and the legal texts the
site shows, the knowledge the assistant's help chat answers from
(`GET /internal/help/knowledge`), the contact form and the news. It keeps the contact page's messages as
`contact.sent` events in its own database's outbox until they're published, and a week after
(notifications emails them); the ones sent from a user's email go with the account
(accounts' `user.deleted`, at `/internal/events`) and are in its export (`/internal/users/{id}/export`), with Turnstile and per-address limits (`CONTACT_*`) on the form. It
also keeps the news posts and their translations (`news`, `news_translations`): the news page,
the admin zone's news tab, the bell's notification for each post (`notification.requested`, taken
back with `notification.news_withdrawn`), the post's English and missing
languages sent to generation, whose translations come back as `news.translated` events (at
`/internal/events`), the post's English for notifications (`/internal/news/{id}`) and the bell's
titles (`/internal/news/titles`); a
daily schedule (`/internal/schedules/news`) sends posts still missing a language again. A
one-off job copied library's news rows (`python -m site_content.jobs.copy_from_library`, safe to
repeat). What it does:
[the site](../../docs/features/site.md).

Its Python package is `site_content`, not `site`: `site` is a module of Python's own, loaded when
the interpreter starts, so a package of that name would hide it.

## Layout

```
src/site_content/
├── main.py, config.py      # App wiring; settings
├── api/v1/                 # Routes (the folder name only: URLs have no extra /v1)
├── api/dependencies.py     # Calls from other services
├── core/                   # db.py (engine, Session), security.py (service tokens)
├── handlers/               # Pub/Sub events (accounts' `user.deleted`, generation's
│                           # `news.translated`); dispatch.py picks one
├── services/               # The help knowledge, contact, news, deletion and export, the outbox;
│                           # each opens its transaction
├── repositories/           # Database queries (news, the outbox); take the session, never commit
├── models/, schemas/       # SQLAlchemy tables; request and response models
├── helpers/, constants/    # Pure functions (guides, legal versions); fixed values, the FAQ
├── integrations/           # billing (public prices), generation (translations), Redis
├── jobs/                   # One-off: the copy of library's news rows
├── prompts/                # The platform guide (help.py) and the help knowledge's frame
│                           # (help_knowledge.py: guide, FAQ, prices, terms, privacy)
├── page_guides/            # Each page's guide, one JSON file per language
├── legal_versions/         # Every published version of the legal texts
└── legal_archive.py        # `python -m site_content.legal_archive`: keeps a new legal version
tests/unit/, tests/integration/   # Mirror src/
migrations/                       # Alembic
```

Its public routes are under `/api/site/` (`/api/site/help/faq`, `/help/guide`, `/help/pages/...`,
`/help/guides...`, `/help/legal/...`, `/help/contact`, `/news`, `/superadmin/news...`).

The help articles come from `frontend/content` at the repo root (`constants/help.py`); the
images copy it to `/frontend/content`, at the same place relative to the code.

`src/` is on the path (`PYTHONPATH` in the Dockerfile, `pythonpath` for pytest,
`prepend_sys_path` for Alembic), so the package imports as `site_content`
(`site_content.api.v1.help`).

## Commands

```bash
docker compose up -d --build site                # the service and its migrations
cd services/site && uv run pytest                # unit tests
scripts/integration.sh site                      # integration tests (real Postgres and Redis)
```
