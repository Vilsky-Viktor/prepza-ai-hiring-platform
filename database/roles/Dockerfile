# The db-roles job: gives each service its own Postgres user (src/db_roles.py). Built from this
# folder; it belongs to no service, so it has its own small image.
FROM python:3.14-alpine@sha256:f6a589d43c42b9e7f7dc67a12d37132491f362859a5d750607710cc56da3bc72 AS python

# Installs the locked packages. uv stays in this stage and in dev, out of production's image.
FROM python AS base

# Pinned by digest; Dependabot proposes updates.
COPY --from=ghcr.io/astral-sh/uv:0.12@sha256:3af4716e991d6956a41e573eab705d0ee08500cd829ed30293eb8472f372c65a /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never

# The image mirrors the repo layout, as the services' do (scripts/integration.sh mounts the tests).
WORKDIR /database/roles
ENV PATH="/database/roles/.venv/bin:$PATH" PYTHONPATH=/database/roles/src

COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-dev

# Development: docker-compose.yml mounts the source; scripts/integration.sh runs the tests here.
FROM base AS dev

ENV PYTHONPYCACHEPREFIX=/tmp/pycache

CMD ["python", "-m", "db_roles"]

# Production: the code and the installed environment, not uv.
FROM python AS prod

WORKDIR /database/roles
ENV PATH="/database/roles/.venv/bin:$PATH" PYTHONPATH=/database/roles/src
COPY --from=base /database/roles/.venv ./.venv
COPY src ./src

# An unprivileged user that can read the code but not change it. Bytecode is compiled now, as
# that user can't write it later.
RUN python -m compileall -q src && adduser -D -H -u 10001 app
USER app

CMD ["python", "-m", "db_roles"]
