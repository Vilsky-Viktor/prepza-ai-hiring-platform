# Built from the repo root (see docker-compose.yml), so the shared package can be copied in.
FROM python:3.14-alpine@sha256:f6a589d43c42b9e7f7dc67a12d37132491f362859a5d750607710cc56da3bc72 AS python

# Installs the locked packages. uv stays in this stage and in dev, out of production's image.
FROM python AS base

# Pinned by digest; Dependabot proposes updates.
COPY --from=ghcr.io/astral-sh/uv:0.12@sha256:3af4716e991d6956a41e573eab705d0ee08500cd829ed30293eb8472f372c65a /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never

# The image mirrors the repo layout, so pyproject.toml's path source (../../packages/common)
# finds the shared package.
WORKDIR /services/rounds
# The environment's commands (uvicorn, alembic, python) run directly, not through uv, so they get
# the container's signals.
ENV PATH="/services/rounds/.venv/bin:$PATH"

COPY packages/common /packages/common
COPY services/rounds/pyproject.toml services/rounds/uv.lock services/rounds/.python-version ./
RUN uv sync --locked --no-dev

EXPOSE 8000

# Development: docker-compose.yml mounts the source, and the server reloads on change.
FROM base AS dev

# Bytecode stays out of the mounted source, so tests run on the host can't leave a half-written
# .pyc that a reloading container then fails to import. Polling sees changes from the host.
ENV PYTHONPYCACHEPREFIX=/tmp/pycache WATCHFILES_FORCE_POLLING=true

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header", \
    "--reload", "--reload-dir", "app", "--reload-dir", "/packages/common/src"]

# Production: the source is part of the image, uv isn't. Migrations run in a one-off container
# (alembic upgrade head) before the API starts.
FROM python AS prod

WORKDIR /services/rounds
ENV PATH="/services/rounds/.venv/bin:$PATH"
# Only the installed environment and the shared package it links to (an editable install).
COPY --from=base /packages/common /packages/common
COPY --from=base /services/rounds/.venv ./.venv

EXPOSE 8000

COPY services/rounds/alembic.ini ./
COPY services/rounds/migrations ./migrations
COPY services/rounds/app ./app
# The site's content, whose guide articles the help routes serve, at the same place relative to
# the code as in the repo.
COPY frontend/content /frontend/content

# An unprivileged user that can read the code but not change it. Bytecode is compiled now, as
# that user can't write it later.
RUN python -m compileall -q app && adduser -D -H -u 10001 app
# The commit the image is built from, as the release Sentry tags its errors with.
ARG SENTRY_RELEASE
ENV SENTRY_RELEASE=$SENTRY_RELEASE
USER app

# Cloud Run kills the container 10 seconds after asking it to stop: requests still running
# after 8 are dropped, so the app's shutdown (and Sentry's last reports) still run.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header", \
    "--timeout-graceful-shutdown", "8"]
