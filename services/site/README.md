# site

The public site's content: the FAQ, each page's guide, the guide articles and the legal texts the
site shows, the knowledge the assistant's help chat answers from
(`GET /internal/help/knowledge`), and the contact form. It keeps the contact page's messages as
`contact.sent` events in its own database's outbox until they're published, and a week after
(notifications emails them); accounts deletes and exports the ones sent from a user's email
(`/internal/users/{id}`), with Turnstile and per-address limits (`CONTACT_*`) on the form. What it does:
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
├── services/               # The help knowledge, contact, deletion and export, the outbox;
│                           # each opens its transaction
├── repositories/           # Database queries (the outbox); take the session, never commit
├── models/, schemas/       # SQLAlchemy tables; request and response models
├── helpers/, constants/    # Pure functions (guides, legal versions); fixed values, the FAQ
├── integrations/           # billing (public prices), Redis
├── prompts/                # The platform guide's texts, sent with the help knowledge
├── page_guides/            # Each page's guide, one JSON file per language
├── legal_versions/         # Every published version of the legal texts
└── legal_archive.py        # `python -m site_content.legal_archive`: keeps a new legal version
tests/unit/, tests/integration/   # Mirror src/
migrations/                       # Alembic
```

Its routes keep rounds' public addresses (`/api/rounds/help/faq`, `/help/guide`,
`/help/pages/...`, `/help/guides...`, `/help/legal/...`, `/help/contact`), which the gateway and the load
balancer send to it (`locals.site_paths`); it serves each at the same path under `/api/site/`
too.

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
