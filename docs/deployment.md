# Deployment

Production runs on Google Cloud in `europe-west1`, set up by Terraform in [`infra/`](../infra/README.md). The infra README also has the one-time bootstrap steps, the GitHub setup for deploys and the restore drill.

- [Production images](#production-images)
- [Migrations](#migrations)
- [Error reporting](#error-reporting)
- [CI/CD](#cicd)
- [Releasing](#releasing)
- [Rolling back](#rolling-back)
- [Dependencies](#dependencies)

## Production images

Every app Dockerfile (on Alpine) has a `prod` target, with the code built in and no reload. The API images are built from the repo root, because they include `packages/common`:

```bash
docker build --target prod -f services/library/Dockerfile -t prepza-library .   # also generation, rounds, companies, billing, notifications, ats, api, assistant
docker build --target prod -t prepza-frontend \
  --build-arg NEXT_PUBLIC_FIREBASE_API_KEY=... --build-arg NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=... \
  --build-arg NEXT_PUBLIC_FIREBASE_PROJECT_ID=... frontend
```

Never set `FIREBASE_AUTH_EMULATOR_HOST` in production.

Terraform passes none of generation's settings to Google Cloud; production runs on their defaults (see [Generation settings](generation.md#generation-settings) and [infra/README.md](../infra/README.md#notes)). The assistant runs on its defaults too (`ASSISTANT_MODEL`, `ASSISTANT_REASONING_EFFORT`, `ASSISTANT_RETENTION_DAYS`). It gets `SITE_URL` and `FIREBASE_WEB_API_KEY` (the `firebase_web_api_key` variable) for AI apps over MCP, whose endpoint and OAuth paths the load balancer sends to it at the site's root; its account needs to read Firebase accounts and sign as itself (`infra/terraform/iam.tf`, see [AI apps over MCP](features/mcp.md)). Usage limits, and the values tuned with them (seconds a question by level, generation's AI calls at once and a second, the multi-answer share, the questions generated per topic, the topics and subtopics a test has, the share of Resend's quota kept from bulk sends, the monthly AI budget), aren't settings: each starts at its default in `prepza_common.limits.limit_list` and a superadmin changes it in the admin zone's Controls tab ([Admin zone](features/admin-zone.md#limits)).

## Migrations

- Run each API's migrations once before it starts: `alembic upgrade head` (production images have no `uv`).
- Each of the 9 API services has them (library, generation, rounds, companies, billing, notifications, ats, api, assistant); the generation worker and the bell stream share generation's and notifications' databases. In Google Cloud, each runs as a `<service>-migrate` job, after the `db-roles` job that gives each service its own database user.
- Migrations only go forward, so keep them additive for rollbacks to stay safe.
- **Waiting to be dropped:** a table a migration replaced stays until no version that reads it can be rolled back to; then a later migration drops it.
  - notifications `legal_notices`: copied into `bulk_sends` by 0009. Once every deployed version and any rollback target is at 0009 or later (no running code imports it), add a migration that drops it; its `downgrade` recreates the empty table. Check first that every row has its `bulk_sends` copy (`kind = 'legal_' || document`, `about = version`).

## Error reporting

Errors go to Sentry when its DSN is set; empty, nothing is sent. Emails are scrubbed from every event, and URLs are cut to their host, so web hook addresses (which can carry secrets) never reach it.

When a page fails, the error page offers **Report**: what the user writes there goes to Sentry's User Feedback, attached to that error, with no email.

| Setting | What it sets |
|---|---|
| `BACKEND_SENTRY_DSN` | The DSN for the backend services |
| `FRONTEND_SENTRY_DSN` | The DSN for the frontend, a build argument |
| `ENVIRONMENT` | The environment's name, which Sentry's error reports and Langfuse's traces carry: `production` in Google Cloud (Terraform sets it, and CI builds the frontend's images with `NEXT_PUBLIC_ENVIRONMENT=production`), `development` locally. Paddle's account is chosen separately (`PADDLE_ENVIRONMENT`), on purpose |
| `SENTRY_TRACES_SAMPLE_RATE` | The share of requests traced (default 0.1). Uptime checks (`/ready`, `/health`), scheduled jobs and Pub/Sub events (`/internal/`) aren't traced unless a traced request made the call; their errors are still reported |
| `SENTRY_RELEASE` | The release events are tagged with: the commit, built into every image by CI (services read it at runtime; the frontend's Sentry plugin names it at build time). The frontend's build also uses it as Next.js's `deploymentId`, so a page left open across a deploy reloads in full on its next navigation instead of asking for files the new build no longer has |
| `SENTRY_AUTH_TOKEN`, `SENTRY_ORG`, `SENTRY_PROJECT` | Optional, for the frontend build to upload its source maps, so frontend stack traces show the original code: CI passes the organization and project from the GitHub variables of the same names, and the token from the `SENTRY_AUTH_TOKEN` secret as a build secret, which stays out of the image. Without the token, nothing uploads |

Events carry user ids only, with emails scrubbed.

## CI/CD

| When | What runs |
|---|---|
| A push to a pull request | CI ([`ci.yml`](../.github/workflows/ci.yml)) and the fast checks ([`checks.yml`](../.github/workflows/checks.yml)); a newer push cancels the runs for the previous one |
| A merge to `main` | CI again on the merged code, then the production images are pushed, tagged with the commit: the changed ones are built, the others are the last passing commit's images with this commit's tag added. Nothing is deployed |
| A `v*` tag on such a commit | [`deploy.yml`](../.github/workflows/deploy.yml): checks the tag is on `main` and CI and the checks passed on it, tags that commit's images with the version (no rebuild), runs the migrations, deploys every service by the images' digests, smoke-tests the site and creates a GitHub release |
| Actions → Deploy → Run workflow with an earlier tag | Redeploys that version: a rollback. Migrations run only when **Run migrations** (`migrate`) is ticked |

What CI tests is in [Testing](testing.md#ci).

## Releasing

To release, tag the last commit of a push to `main` once CI has passed on it:

```bash
git tag v1.4.0 && git push origin v1.4.0
```

The one-time GitHub setup (tag protection, an optional approval for deploys) is in [infra/README.md](../infra/README.md#deploys).

## Rolling back

Run Actions → Deploy → Run workflow with an earlier tag. It redeploys that version. Migrations run only when **Run migrations** (`migrate`) is ticked.

## Dependencies

- Workflow actions are pinned by commit, and CI's `uv` by version.
- Dockerfile base images, the `uv` image the services copy, and the local and CI stack's images (`compose/`) are pinned by version and digest; the Auth emulator's `firebase-tools` is pinned by version and updated by hand (Dependabot doesn't see it).
- The frontend's and the services' packages are locked (`pnpm-lock.yaml`, each `uv.lock`) and installed only from the lock: CI and the images use `uv sync --locked`, which fails when a lock no longer matches its `pyproject.toml`, and `pnpm install --frozen-lockfile`. pnpm (its version is `packageManager` in `frontend/package.json`) also refuses, by `frontend/pnpm-workspace.yaml`, a version published less than a day ago, one that lost its earlier releases' provenance and sub-dependencies from git or tarball URLs, and runs install scripts only for the packages its `allowBuilds` allows.
- Dependabot ([`.github/dependabot.yml`](../.github/dependabot.yml)) opens weekly pull requests to update all of them, grouped, with minor and patch versions only; a major version is planned by hand.
- The dependency audit ([`.github/workflows/audit.yml`](../.github/workflows/audit.yml)) fails when a package the frontend or a service ships has a known high-severity vulnerability (`pnpm audit`, `pip-audit`), on every push and every Monday. Its gitleaks job fails when any commit carries a secret.
- Each production image CI builds is scanned by Trivy (pinned by commit and version, settings in [`trivy.yaml`](../trivy.yaml)): a high or critical vulnerability with a fix in its OS packages fails the run. Images of unchanged parts aren't built then; the dependency audit builds and scans every image each Monday.
- The containers run their commands (`uvicorn`, `alembic`, `python`) directly from the service's environment, so the server gets the container's signals. `uv` installs the packages in a build stage and stays out of the production image, which gets only Python, the environment and the code.
