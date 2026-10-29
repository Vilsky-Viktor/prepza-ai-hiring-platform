# Testing

prepza has unit, integration, browser, end-to-end and load tests, plus offline evals of model quality. CI runs most of them on every pull request (see [CI](#ci)).

- [Test suites](#test-suites)
- [Unit tests and lint](#unit-tests-and-lint)
- [Integration tests](#integration-tests)
- [Smoke test](#smoke-test)
- [Browser tests](browser-tests.md): [the site they open](browser-tests.md#the-browser-tests-site), [signed-out pages](browser-tests.md#browser-tests-of-the-signed-out-pages), [signed-in pages](browser-tests.md#browser-tests-of-the-signed-in-pages)
- [Translations](#translations)
- [End-to-end test](#end-to-end-test)
- [Load tests](#load-tests)
- [Model and prompt evals](#model-and-prompt-evals)
- [CI](#ci)

## Test suites

| Suite | Command | Needs |
|---|---|---|
| Python unit tests | `cd services/rounds && uv sync && uv run pytest` | Nothing running |
| Python lint and format | `uvx ruff@0.16.10 check ...` (below) | Nothing running |
| File size | `scripts/check_file_size.sh` | Nothing running |
| Migration safety | `scripts/check_migrations.py` (its tests: `uvx --with pytest pytest scripts/tests`) | Nothing running |
| Gateway config | `uvx --with pytest pytest scripts/tests/test_nginx_conf.py`: a block with its own `add_header` or `proxy_set_header` repeats the server's | Nothing running |
| Workflows, images and alerts | `uvx --with pytest pytest scripts/tests`: every workflow starts read-only and every job has a timeout; images pinned by digest, installed from the lock, no `uv` and no root in production; every alert's severity and runbook section | Nothing running |
| Frontend lint, types, translations and unit tests | `cd frontend && pnpm install && pnpm lint && pnpm typecheck && pnpm check:messages && pnpm test` | Nothing running |
| Smoke test | `./e2e_tests/smoke.sh` | The running stack |
| Integration tests | `./scripts/integration.sh` | The running stack |
| Signed-out pages ([browser tests](browser-tests.md)) | `./e2e_tests/pages.sh` | The running stack |
| Signed-in pages ([browser tests](browser-tests.md)) | `./e2e_tests/signed-in.sh` | The running stack |
| Translations | `cd frontend && pnpm check:messages` | Nothing running |
| End-to-end | `python3 e2e_tests/flow.py` | `OPENAI_API_KEY` |
| AI apps over MCP | `python3 e2e_tests/mcp.py` | The running stack |
| Load tests | `./e2e_tests/load.sh candidates` | The local stack only |

## Unit tests and lint

Each Python service (and `packages/common`) keeps:

- `tests/unit`: fakes, no services needed,
- `tests/integration`: real Postgres and Redis,
- the shared setup in `tests/conftest.py`.

```bash
# Unit tests of each Python service, and of the shared package (packages/common)
cd services/rounds && uv sync && uv run pytest

# Python lint and format, as CI runs them (ruff's version is pinned in CI)
uvx ruff@0.16.10 check services packages evals && uvx ruff@0.16.10 format --check services packages evals

# Frontend: lint, types, translations, and unit tests of the pure helpers (frontend/tests, vitest)
cd frontend && pnpm install && pnpm lint && pnpm typecheck && pnpm check:messages && pnpm test
```

Vitest runs files and tests in a random order and restores spies, stubbed globals and env after each test, so no test leans on another's leftovers; it prints the seed, and `pnpm test --sequence.seed=<seed>` repeats an order.

Besides the helpers, vitest checks rules the code must keep: `tests/messages/numbers.test.ts` (every plural has its language's forms, no bare number in a message), `tests/styles/logical-direction.test.ts` (no physical `ml-`, `pl-`, `left-`, `text-left` or inline `left:`, so pages mirror right to left) and `tests/content/articles.test.ts` (the articles' front matter, first heading and slugs, and every translation with the original's sections and links).

## Integration tests

Each service's `tests/integration` runs against the running stack's real Postgres and Redis, in a `<service>_test` database created and dropped for the run. Every test starts clean (`prepza_common.db.clean_start`): before it, the tables the migrations left empty are truncated, Redis database 15 is flushed and work an earlier test left running is ended; rows the migrations seed stay. Nothing outside the `_test` databases and Redis database 15 is touched. `db-roles` (the database users job, `database/roles`) runs with them: its test makes and drops its own throwaway database and users.

```bash
./scripts/integration.sh            # or: ./scripts/integration.sh rounds library
```

Each service's `tests/integration/api/test_access_matrix.py` is its access matrix (IDOR): every route taking the id of something a company or a user owns, found from the app, is called against the real database by its owner (let through), another company's owner or another user with the owner's ids (refused), on a route with several ids that other owner with their own ids but one of the owner's (refused), a viewer of the company changing something (refused), nobody signed in (401) and, on superadmin routes, anyone but the superadmin (404). Calls to other services stay in the test: companies' membership check is answered from the test's own roles, anything else gets a 503. A new route taking an id fails the matrix until it's covered, or listed with why it takes no owned id (a link's token, public content); a route that differs on purpose (an owner-only read) is listed with its reason. The shared code is `packages/common/tests/access_matrix.py`; `test_route_guards.py` beside it in each service's unit tests catches a route that runs no guard at all.

```bash
PYTEST_ADDOPTS="-k access_matrix" ./scripts/integration.sh companies
```

## The assistant's OpenAPI snapshots

The assistant builds its tools from snapshots of the other services' OpenAPI descriptions in `services/assistant/src/assistant/openapi/`. After changing a route of companies, billing, library, notifications, ats, api, rounds or accounts, refresh them with the stack running and commit the result; CI's stack job runs the script and fails when a snapshot differs.

```bash
./scripts/assistant-openapi.sh
```

## The generation graph's diagram

The diagram of the generation graph in [Generation and question quality](generation.md#generation-pipeline) is drawn from the compiled LangGraph graph. After changing the graph (`services/generation/src/generation/services/graph.py`), redraw it and commit the result; generation's unit test `test_graph_diagrams.py` fails while the doc differs. It needs nothing running and sends the graph nowhere (the diagram is Mermaid text, which GitHub draws).

```bash
./scripts/graph-diagrams.sh
```

## Smoke test

A smoke test against a running stack:

```bash
./e2e_tests/smoke.sh
```

## Browser tests

Playwright tests of the signed-out and signed-in pages, run on a production build of the frontend
in parallel: [Browser tests](browser-tests.md).

## Translations

Every language has exactly the keys of `en.json`, with the same arguments and rich-text tags, valid ICU syntax and an `other` form in every plural. In a language whose `one` form also covers other numbers (Filipino's 3, French's 0, Russian's 21), a plural that shows the number uses `=1` for exactly one, so 3 never reads as "your first one". CI runs it in the frontend job.

```bash
cd frontend && pnpm check:messages     # or name languages: pnpm check:messages de fr
```

## End-to-end test

An end-to-end run with a real generation. It needs `OPENAI_API_KEY` and costs a few cents and a few minutes.

1. A company generates an interview and invites a candidate.
2. The candidate takes it from the invite link.
3. The company sees the scorecard and pays for that candidate.

Its accounts, company and data are deleted at the end, however the run ends.

```bash
python3 e2e_tests/flow.py
```

## AI apps over MCP

`e2e_tests/mcp.py` connects an app to the running stack through the gateway, as Claude or ChatGPT would: it registers itself without a secret, is allowed on the consent page's API with a throwaway emulator user's token (its email marked verified, as Google's are), exchanges the code with PKCE (a wrong verifier and a second exchange are refused), lists the tools (without the account's and a company's deletion), calls `get_me`, `create_company` and `list_companies` as the user, signs an agent in with company API keys (one without the mcp permission is refused; one with it and `candidates:read` lists only its tools, reads its company and is refused an invite), refreshes (the old tokens stop working), revokes, and has the user disconnect a second app. The account is deleted at the end, with its company and connections. No OpenAI; CI runs it after the integration tests. Standard library only; its client (HTTP, the emulator user, OAuth and JSON-RPC calls) is `e2e_tests/helpers/mcp_client.py`:

```bash
python3 e2e_tests/mcp.py
```

The assistant's integration tests also connect an app in-process with the MCP SDK's own OAuth client (`tests/integration/test_mcp.py`).

## Load tests

Load tests with k6, in its Docker image, against a local stack only: never production. Besides a run by hand, `.github/workflows/load.yml` runs every scenario with its default settings each Monday (and by hand from Actions) on a stack started on the runner, as CI's smoke job starts it.

- Scenarios: many candidates taking a test, owners on the dashboard, the public pages.
- Throwaway users, companies and tests from local templates, all deleted and counted afterwards.
- Settings, thresholds and results are in [e2e_tests/load/README.md](../e2e_tests/load/README.md).

```bash
./e2e_tests/load.sh candidates      # or: dashboard, public; VUS=20 ITERATIONS=2 ./e2e_tests/load.sh candidates
```

## Model and prompt evals

Model and prompt quality is tested offline with the prepared datasets, judge prompts and metrics in [evals/](../evals/README.md): question generation and its checks, and the assistant's page context (with it and without it, on throwaway data).

## CI

CI runs all of these except the end-to-end test, which needs an OpenAI key, and the load tests: the fast checks of the whole repo on every change (`checks.yml`), the tests and images only for what changed (`ci.yml`).

- A service counts as changed when its folder or `packages/common` changed; the frontend, when `frontend/` did. A change to `ci.yml`, `scripts/ci_changes.sh` (which works this out) or `.python-version` counts as everything.
- A pull request compares with its base. `main` compares with the last commit CI passed on, so a failed run's changes are tested and built by the next one.
- Each changed part's unit tests run and its production image is built. A changed frontend also gets lint, types and the translations check (`pnpm check:messages`). On `main`, an unchanged part's image is the last passing commit's, tagged with the new commit too.
- `checks.yml`, on every change: Ruff and the file size check (`scripts/check_file_size.sh`: no hand-written file over 300 lines, CLAUDE.md rule 2), the scripts' tests (`scripts/tests`) and the migration check (`scripts/check_migrations.py`): a new migration that builds an index without `CONCURRENTLY`, adds a foreign key or `CHECK` without `NOT VALID`, changes a column's type in place, sets `NOT NULL` without a validated check or renames, on a table that already exists, fails it (`.claude/rules/database.md`). Ruff and the frontend's ESLint also fail a function over complexity 15 (and, in Python, over 12 branches or 50 statements); tests and migrations are exempt in Python, the generated API types in the frontend.
- `checks.yml` also runs Terraform's format check, `terraform validate` (no credentials, no state, Terraform's version pinned) and TFLint (`infra/terraform/.tflint.hcl`: Terraform's recommended rules, and a type and description on every variable and output).
- And ShellCheck on every shell script (`.shellcheckrc` also asks for `[[ ]]` in bash and quotes around every variable), and actionlint and zizmor on the workflows (tools pinned by version and checksum). Locally: `shellcheck $(git ls-files '*.sh')`, `actionlint` and `uvx zizmor@1.31.1 --offline .github`.
- The dependency audit (`.github/workflows/audit.yml`) runs on every change and every Monday: `pip-audit`, `pnpm audit --prod`, and gitleaks over the whole history (`.gitleaks.toml` allows tests' made-up keys and placeholders; mark another made-up value with a `gitleaks:allow` comment). On Mondays it also builds and scans every production image's OS packages with Trivy.
- It starts the whole stack for the smoke, integration, MCP, page and signed-in tests when any part changed, or `e2e_tests/`, `gateway/`, `database/`, `firebase/`, `scripts/`, `compose/` or `docker-compose.yml` did. A change to docs alone skips it.
- Its stack has no templates, so before the signed-in tests it adds a small English one (`e2e_tests/signed-in/seed/template.py`, no OpenAI).
- Its superadmin is a CI-only emulator account.
- On failure, the screenshots and traces are kept as the run's `signed-in-test-results` artifact.

When CI runs, and how releases follow it, is in [Deployment](deployment.md#cicd).
