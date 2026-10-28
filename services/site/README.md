# site

The public site's content. It keeps what it holds in its own database.

Its Python package is `site_content`, not `site`: `site` is a module of Python's own, loaded when
the interpreter starts, so a package of that name would hide it.

## Layout

```
src/site_content/
├── main.py, config.py      # App wiring; settings
├── api/dependencies.py     # Calls from other services
├── core/                   # db.py (engine, Session), security.py (service tokens)
├── models/                 # SQLAlchemy tables
├── constants/              # Fixed values
└── integrations/           # Redis
tests/unit/, tests/integration/   # Mirror src/
migrations/                       # Alembic
```

`src/` is on the path (`PYTHONPATH` in the Dockerfile, `pythonpath` for pytest,
`prepend_sys_path` for Alembic), so the package imports as `site_content`.

## Commands

```bash
docker compose up -d --build site                # the service and its migrations
cd services/site && uv run pytest                # unit tests
scripts/integration.sh site                      # integration tests (real Postgres and Redis)
```
