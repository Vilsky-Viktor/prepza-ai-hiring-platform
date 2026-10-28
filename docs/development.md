# Development

How to run prepza locally, the settings it reads, and the everyday commands.

- [Running locally](#running-locally)
- [Local addresses](#local-addresses)
- [Settings](#settings)
- [Databases and migrations](#databases-and-migrations)
- [The local stack](#the-local-stack)
- [Everyday commands](#everyday-commands)
- [Project conventions](#project-conventions)

## Running locally

Requirements: Docker with Compose (on a Mac, Docker Desktop with VirtioFS file sharing and at
least 12 GB of memory), and an OpenAI API key. The frontend runs Next.js's dev server with
Turbopack and picks up file changes from the bind mount through VirtioFS's file events, without
polling.

```bash
cp .env.example .env
# Set OPENAI_API_KEY in .env.
docker compose up --build
```

## Local addresses

| URL | What |
|---|---|
| http://localhost:8090 | The app |
| http://localhost:4100 | Firebase Auth emulator UI (sign-in creates fake accounts here) |
| http://localhost:8125 | Mailpit: every email sent locally, when `RESEND_API_KEY` is empty |

To try the app on a phone, connect it to the same Wi-Fi and open `http://<your computer's local IP>:8090` (on a Mac, `ipconfig getifaddr en0` prints it). Signing in works there too: the page reaches the sign-in emulator on the host it was opened from, and the dev server serves its scripts to local-network addresses (`allowedDevOrigins` in `frontend/next.config.ts`).

Without `RESEND_API_KEY`, emails go to Mailpit instead of real inboxes. To send real ones, see [Notifications and emails](features/notifications.md#sending-real-emails).

## Settings

Settings live in `.env`, copied from [`.env.example`](../.env.example). Apart from `OPENAI_API_KEY`, the values work locally as they are:

| Setting | What it is |
|---|---|
| `POSTGRES_PASSWORD` | The local Postgres password |
| `SERVICE_SECRET` | Signs calls between services; at least 32 characters |
| `FIREBASE_PROJECT_ID` | A `demo-` project, which lets the services (`FIREBASE_AUTH_EMULATOR_HOST`) and the browser (`NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_URL`) use the Auth emulator |

Settings are described with the feature they shape:

| Topic | Page |
|---|---|
| Generation, models, rate limits | [Generation and question quality](generation.md#generation-settings) |
| Langfuse (every AI call's traces, the chats' votes) | [Generation settings](generation.md#generation-settings), [In-app assistant](features/assistant.md#settings) |
| Paddle | [Credits and payments](features/billing.md#setting-up-paddle) |
| Resend, Mailpit, `SITE_URL`, `CONTACT_EMAIL` | [Notifications and emails](features/notifications.md#emails) |
| `EMAIL_LINK_SECRET` | [Notifications and emails](features/notifications.md#unsubscribing) |
| Email limits | [Candidates](features/candidates.md#email-limits) |
| Help chat and contact form limits | [Public site](features/site.md#faq-and-help-chat) |
| Every usage limit and the values tuned with them, such as the questions generated per topic, the topic caps and the monthly AI budget (not settings: edited in the admin zone) | [Admin zone](features/admin-zone.md#limits), [Credits and payments](features/billing.md#ai-usage-and-limit-hits) |
| `ATS_ENCRYPTION_KEY` | [ATS integrations](features/ats.md#connecting-an-ats) |
| `API_ENCRYPTION_KEY` | [Public API](features/api.md#settings) |
| `FIREBASE_WEB_API_KEY` (AI apps over MCP) | [AI apps over MCP](features/mcp.md#settings) |
| `SLACK_CLIENT_ID`, `SLACK_CLIENT_SECRET`, `SLACK_ENCRYPTION_KEY` | [Notifications and emails](features/notifications.md#setting-up-slack) |
| `SUPERADMIN_EMAILS` | [Admin zone](features/admin-zone.md) |
| `ANALYTICS_SALT` | [Architecture](architecture.md#funnel-events) |
| Sentry, search engine verification | [Deployment](deployment.md#error-reporting) and [Public site](features/site.md#search-engines) |

## Databases and migrations

- Each service connects as its own Postgres user (named after its database), which owns only that database, as in production: the short-lived `db-roles` container (library's `db_roles` job) creates the users and moves ownership to them before any migration; it's safe to repeat. `prepza` is the admin; the integration tests use it to make their `<service>_test` databases.
- Each API's database migrations run once, in a short-lived `*-migrate` container, before the API starts.
- A Postgres volume made before a database was added needs that database created once, for example:

  ```bash
  docker compose exec postgres createdb -U prepza ats
  ```

  The next `docker compose up` gives it to its service's user.

- Docker marks an API healthy only when `/ready` confirms its database answers. Redis isn't checked, so a Redis outage doesn't stop a service from starting.

## The local stack

[`docker-compose.yml`](../docker-compose.yml) is for local development only. It includes the files
in [`compose/`](../compose), split by kind: `infrastructure.yml` (Postgres, Redis, the Pub/Sub and
Firebase Auth emulators, Mailpit), `services.yml` (library, generation, rounds, companies),
`integrations.yml` (billing, notifications, ats, api, assistant, accounts), `web.yml` (the frontend, the gateway, the
scheduler); each API service and its migrations extend `base.yml`. Together they:

- builds each image's `dev` target,
- mounts the source, so servers reload on change (a server reloads only once its open requests
  end: a code change during a generation leaves `generation-worker` finishing that run first, and
  until then it takes no new job; one started meanwhile is lost locally and waits in "queued", so
  start it again after the run),
- enables the Firebase emulator,
- runs Google's Pub/Sub emulator and a small `scheduler` container (see [Architecture](architecture.md#background-work)).

The frontend keeps its `node_modules` in a volume. After a frontend dependency changes:

1. run `docker compose build frontend`,
2. remove the `prepza_frontend-modules` volume,
3. start again.

Paddle and Resend reach local webhooks only through a tunnel, for example `cloudflared tunnel --url http://localhost:8090`.

Prices follow the visitor's country, which the load balancer gives in production. Locally, set a `test_country` cookie on `localhost:8090` (`document.cookie = "test_country=DE"`, or `GB`; none means US dollars) and the gateway passes it on as that country ([Currencies](features/billing.md#currencies)). A person's and a company's currency are saved the first time billing sees them with a country, so use a new account or company to see another country's default.

## Everyday commands

```bash
# After changing an API: regenerate the frontend's API types (needs the stack running)
cd frontend && pnpm api-types

# Give template topics without an embedding one
docker compose exec generation uv run --no-sync python -m generation.jobs.embed_templates

# Tag the language of question examples saved before they were tagged (once after deploying it)
docker compose exec generation uv run --no-sync python -m generation.jobs.tag_code_languages
# Re-tag "text" examples that are in a notation after all (examples of several files; once)
docker compose exec generation uv run --no-sync python -m generation.jobs.tag_code_languages --text

# Rebuild the documents for companies after changing their sources
./scripts/documents/build.sh   # needs uv (for pandoc) and Docker (Chromium prints the PDFs)
```

Tests, lint and the translations check are in [Testing](testing.md).

## Connecting an AI app locally

The MCP server is at http://localhost:8090/mcp ([AI apps over MCP](features/mcp.md)). Allowing an app opens the consent page in the browser, where you sign in with an emulator account.

```bash
# Claude Code
claude mcp add --transport http prepza http://localhost:8090/mcp

# MCP Inspector (in the browser): Streamable HTTP, URL http://localhost:8090/mcp, then Connect
npx @modelcontextprotocol/inspector
```

Claude (claude.ai, the desktop app) and ChatGPT connect from their own servers, so they need the stack at a public HTTPS address (a tunnel to port 8090) with `SITE_URL` set to it.

## Project conventions

See [CLAUDE.md](../CLAUDE.md). In short:

- separate modules for schemas, models, prompts, helpers and constants,
- `main.py` only wires the app,
- at most 300 lines per file,
- the simplest solution that works,
- no business logic on the frontend: rules, thresholds and decisions live in the services.

Claude Code skills for the repo's recurring work live in `.claude/skills/`: `translate` (a text in all 23 languages), `api-types` (the assistant's API snapshots and the frontend's types), `verify` (which suites to run, and the slow dev server), `review-batch` (working through a platform review), `ui-build` (a screen in the app's design language, from its shared components), `ui-check` (screenshots, desktop and phone) and `migration` (an Alembic migration).
