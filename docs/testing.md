# Testing

prepza has unit, integration, browser, end-to-end and load tests, plus offline evals of model quality. CI runs most of them on every pull request (see [CI](#ci)).

- [Test suites](#test-suites)
- [Unit tests and lint](#unit-tests-and-lint)
- [Integration tests](#integration-tests)
- [Smoke test](#smoke-test)
- [Browser tests of the signed-out pages](#browser-tests-of-the-signed-out-pages)
- [Browser tests of the signed-in pages](#browser-tests-of-the-signed-in-pages)
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
| Frontend lint, types, translations and unit tests | `cd frontend && pnpm install && pnpm lint && pnpm typecheck && pnpm check:messages && pnpm test` | Nothing running |
| Smoke test | `./e2e_tests/smoke.sh` | The running stack |
| Integration tests | `./scripts/integration.sh` | The running stack |
| Signed-out pages | `./e2e_tests/pages.sh` | The running stack |
| Signed-in pages | `./e2e_tests/signed-in.sh` | The running stack |
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

## Integration tests

Each service's `tests/integration` runs against the running stack's real Postgres and Redis, in a `<service>_test` database created and dropped for the run. Every test starts clean (`prepza_common.clean_start`): before it, the tables the migrations left empty are truncated, Redis database 15 is flushed and work an earlier test left running is ended; rows the migrations seed stay. Nothing outside the `_test` databases and Redis database 15 is touched.

```bash
./scripts/integration.sh            # or: ./scripts/integration.sh rounds library
```

## The assistant's OpenAPI snapshots

The assistant builds its tools from snapshots of the other services' OpenAPI descriptions in `services/assistant/app/openapi/`. After changing a route of companies, billing, library, notifications, ats, api or rounds, refresh them with the stack running and commit the result; CI's stack job runs the script and fails when a snapshot differs.

```bash
./scripts/assistant-openapi.sh
```

## The generation graph's diagram

The diagram of the generation graph in [Generation and question quality](generation.md#generation-pipeline) is drawn from the compiled LangGraph graph. After changing the graph (`services/generation/app/services/graph.py`), redraw it and commit the result; generation's unit test `test_graph_diagrams.py` fails while the doc differs. It needs nothing running and sends the graph nowhere (the diagram is Mermaid text, which GitHub draws).

```bash
./scripts/graph-diagrams.sh
```

## Smoke test

A smoke test against a running stack:

```bash
./e2e_tests/smoke.sh
```

## Browser tests of the signed-out pages

Playwright tests of the signed-out pages, on desktop and phone sizes, in Playwright's Docker image. The pages (`pages.spec.ts`): home, companies, pricing (also in German and Japanese), terms, privacy, documents, FAQ, about, contact, practice, skills tests by role, and the articles (pre-employment testing, AI interviews, a comparison, a guide and their hubs). It also checks that the sign-in dialog offers its two email boxes, unticked.

They check:

- no console errors,
- no sideways scroll,
- the same page width everywhere,
- the footer at the end,
- lowercase titles (articles keep their capitals).

`landing.spec.ts` checks the home page: every section in order and within the window on a desktop and a phone, in every language too; with reduced motion every picture a still frame; the hero's box asking a visitor to sign in to start an interview; the hero's video button playing the video in a window; the pricing section's top-ups and free candidates from billing's catalog, with the receipt paying for the top-up with the lowest price per candidate; the comparison's price range from the catalog; the closing buttons to the agent, the demo videos, the FAQ and the guides. `landing-create.spec.ts` checks the create section's panels and questions per topic, and each "create an interview" button going back up to the job description box, focused. Other specs check the catalog's free candidates on the pricing page (`pricing.spec.ts`), smooth scrolling and back to top (`scroll.spec.ts`), the API docs (`api-docs.spec.ts`), the demo videos link opening YouTube and the footer's "ask agent" (`demos.spec.ts`), and the info button opening its guide (`page-help.spec.ts`). `assistant.spec.ts` checks the assistant signed out: FAQ answers only (stubbed: no OpenAI), a sign-in card when asked, a failed answer's Try again, a reload in the middle of a chat, and the panel and a dialog opening and closing fully with and without reduced motion. `phone-layout.spec.ts` checks the public pages on a phone: previews and the home page's box across the screen, the footer one centered column, dialogs across the screen, no keyboard hint on a touch screen, and a practice page starting under its tags. `faq.spec.ts` checks that an FAQ answer's link opens its page in the same tab and stays in the address's language. `footer.spec.ts` checks the footer's three columns of links, the company that runs prepza named in the footer and on the contact page, and where the accessibility statement says to report a problem. `legal-versions.spec.ts` checks that every version of the terms stays readable, saying whether it applies, and shows in the page's language with a link to the binding English. `sign-in.spec.ts` checks that the sign-in card asks about emails only on a browser no one has signed in on. `signed-in-links.spec.ts` checks that links into a company's pages (a scorecard, an interview, a template, a generation) opened signed out ask to sign in instead of "Page not found". `link-errors.spec.ts` checks that an invite says its link is invalid only when it's gone, and offers to try again otherwise. `referral-notice.spec.ts` checks that a referral link is kept in a cookie only once the visitor agrees, and turning it down keeps nothing. `double-submit.spec.ts` checks that a contact message sent twice quickly goes once, and `error-report.spec.ts` that the error page's "Report" sends what the user was doing, and sits in the row of its other buttons on a computer and on its own line under them on a phone. `news.spec.ts` checks the news page in English and German whatever posts exist: indexable, its title, description, canonical and hreflang addresses (x-default too), link-preview picture, `Blog` structured data, the RSS link in its head and its RSS icon; the RSS feed in both languages (content type, channel, items linking to the page); the sitemap listing the page but not the feed; and the footer's news link. `connect.spec.ts` checks the AI app consent page signed out: without a request it says the link expired, with one it asks to sign in first without reading the request, and it isn't indexed. `unsubscribe.spec.ts` checks the unsubscribe page: an invalid link says so, the page isn't indexed, and a candidate's link to a made-up company changes nothing until "Confirm". It signs that link with `EMAIL_LINK_SECRET`, which `pages.sh` passes from `.env` without printing it, and deletes its made-up company's opt-outs from the local notifications database when it ends.

Like every browser test, these check behaviour and data, never the wording: elements are found by role, position, structure or a `data-testid`, and only error messages and data (prices, dates, names the test passes) are matched as text. `seo.spec.ts` checks language addresses and hreflang, titles, preview pictures, noindex on private pages, articles, links and the footer; `seo-templates.spec.ts` checks the template pages: a role page, a template's languages and its page in its language (links and levels), old addresses' redirects, robots.txt and the sitemap, and which templates are indexable (noindex on thin ones). `metadata.spec.ts` checks page descriptions, each page's own title naming the site once, FAQ data (an answer's links as their text) and article data, practice breadcrumbs, the direction of right-to-left template text, the preview picture's noindex and the footer's menu.

Tests that need a template never use the platform's own: each adds its own throwaway templates straight into the library database (`helpers/templates.ts`: a unique title and readable address, topics with subtopics and company and practice questions; at least 3 topics makes one indexable, fewer doesn't), checks only those, and deletes them when it ends. Before a run, a global setup (`global-setup.ts`) deletes the templates and opt-outs a stopped run left, once they're older than 6 hours, so runs at the same time keep each other's. `pages.sh` mounts `.env` read-only for `POSTGRES_PASSWORD`, read without printing it.

```bash
./e2e_tests/pages.sh
```

Extra arguments go to Playwright, for example `--workers=2` when the dev server is slow to compile. Before the tests, the global setup compiles every kind of page they open; a test may take 60 seconds and an assertion waits up to 15, as in the signed-in suite, since the dev server serving every worker at once is slow.

Each run copies the specs into its container (a tar stream, as the signed-in suite does) and installs its own packages there, so runs at the same time don't share `node_modules` or see a file half-edited. Its traces and screenshots land in a folder of their own, `e2e_tests/pages/test-results/<run>` (the script prints it at the end): Playwright empties its results folder when a run starts, so a shared one would lose another run's traces. Folders older than a week are deleted at the next run.

## Browser tests of the signed-in pages

Playwright tests of the signed-in pages, in the same Docker image, against the running stack.

**Signing in.** Users sign in through "Continue with Google" and the Firebase Auth emulator's own sign-in page (local only), optionally ticking the sign-in's email boxes first (`signInAs(email, { noUpdates, promotions })`). The superadmin is the first address in `SUPERADMIN_EMAILS`.

**Test data.** Every test makes throwaway users, companies and interviews. Interviews are made from local templates: no OpenAI. The owner spec adds and deletes its own throwaway templates in the library database.

**What they cover:**

- a company owner making an interview from a template and inviting a candidate,
- inviting candidates with names three ways (one email, a list, a file) and finding one by name, the sign-in filling in a name once with an owner's correction kept, and the invite dialog saying what it couldn't read,
- deleting an interview past the list's first page: it leaves the list at once, and the list goes on loading from the right place,
- a title under three characters and a one-letter company name, refused with the reason,
- a candidate taking an interview, a question's time running out included,
- a "select all that apply" question: ticked with check boxes, a partly right answer earning part of its point, and the scorecard, the practice review and the question lists showing it,
- a candidate leaving the page: only a leave of 2 seconds or more counts, and the results say signals are the browser's report,
- dates in the visitor's own time zone,
- a job ad's shareable link: starting from it, and continuing from the candidate's own link after it's turned off,
- an expired invite, which asks to have it sent again,
- extra time: a candidate given it sees the longer time per question on their invite,
- a candidate whose email isn't confirmed, told to confirm it,
- signing in through each provider's popup (Google, LinkedIn, GitHub) under the site's `Cross-Origin-Opener-Policy`, which the pages send (`y-sign-in-providers.spec.ts`),
- the team and a viewer, and a join link opened while signed in with another email (a warning, no Join),
- a company's action log: the owner sees their own and another member's actions, with who did what, and filters them by member, kind of action and days; an admin and a viewer have no tab, and its page sends them to the company,
- handing a company to an admin, who's told in the bell, and deleting an account that owns a company others joined, which waits, then names the companies deleted with it and their credits,
- removing a company: the dialog says how many credits are lost, and nothing about credits when there are none,
- verification,
- the admin zone's pass rates, stats, pause and maintenance mode (turned off again afterwards),
- the admin zone's support tab: finding a company by its ID, an interview by its link in another language, a candidate by their email in another case and a company by its name (and nothing for something unknown), an account first by its email and by its ID; a company's page: credit history, held credits, members, interviews and action log (who did what), adjusting its credits with a reason the company then sees in its own history, a removal below zero refused with its error, and suspending, lifting, renaming and deleting it (the old companies tab's address leading to support); an interview's page: a failed generation marked, its company, topics and candidates (a grade only for the finished one); a candidate's page: links to the company and interview, start and finish dates once finished, the grade and extra time; an account's page: its companies,
- the admin zone's news tab: the tabs' order, a post written in the dialog (the characters left, an over-long text refused by the API's message), shown in the tab and on the news page with its blue dot and date, shown in a user's bell, turned into a product update campaign from its row, edited with the pencil and deleted with the bin after confirming, leaving the bell. Its posts are deleted at the end, even when it fails,
- the admin zone's campaigns (`zm-campaigns.spec.ts`): a campaign written with the editor (bold and a link), its preview and recipients, a test sent to the superadmin's own address and read back from the local Mailpit (then deleted), its kind changed and the draft deleted; an account's support page showing its address on the suppression list and taking it off; the legal banner for a pending DPA change concerning one throwaway user, closed and still closed after a reload. Nothing is sent to users,
- the admin zone's support pages for people: an address found in another case giving its account first, then its candidates; on the account's page turning off all optional emails (still off after a reload) and marketing refused with its error; on a candidate's page stopping and resuming one inviting company's emails (still stopped after a reload) while the person's own stop has nothing to press; the emails tab's old address leading to support, and "not found" for anyone else on the support, account and candidate pages,
- the candidates' PDF report,
- a viewer emailing a report: an address outside the company refused with the reason, a member's address let through (`f-reports-viewer.spec.ts`),
- a practice result leading to a company's test,
- a talent's practice history, newest first, loading older rounds as it scrolls,
- an interview's settings tab,
- an interview's start page on a computer: the whole interview's minutes from its topics' questions and seconds, the big start button, and the rules card from the screen's top to its bottom, scrolling inside on a short screen (`zo-start-page.spec.ts`),
- a new hard test starting with the hard level's seconds a question, the value changed in the admin zone's Controls reaching the next new hard test, and set back (`zn-level-seconds.spec.ts`),
- a company's brand tab: colors previewed as they're typed, unreadable ones refused, the font and rounding saved with them, and its candidate's invitation in those colors,
- a WebP logo kept as PNG, which every email client shows,
- API keys and web hooks,
- a web hook's signed test event and its delivery log,
- the API's operations: inviting a candidate twice, with and without a client's Idempotency-Key (invited once; the retry is a `200`), a reused key with another body refused, correcting them, extra time, a reminder, finding them by email, the credits, removing them, and a new interview within the app's limits,
- a candidate invited through the API taking the interview without signing in and going back to the company's platform, refused while the company's website isn't verified or the return address is off it,
- a company's own site embedding a candidate's interview and hearing it finish,
- each ATS: Workable's linked jobs, and connecting Greenhouse (with who connected it under its title), Teamtailor, Recruitee and Breezy HR,
- Slack,
- the MCP server: its row and Instructions (the server's address, Claude's and ChatGPT's steps, opening on the dialog itself with Close outside the scrolling body, full height on phones), the connected AI apps (saved straight into the assistant database and deleted at the end) and disconnecting them, and the consent page signed in (an expired request, and a request answered in the browser, denied),
- an AI app connected through the real authorization flow: it registers, the consent page names it, Allow gives it a code that becomes a token once (a second exchange is refused), and the AI apps page lists it,
- an owner stopping AI apps from using the company's data and allowing them again (kept after a reload), the switch right to left in Arabic,
- the company's bell saying when an ATS refuses the results written back, Slack stopped working or a web hook stopped, and opening that page to reconnect,
- the integrations pages on a phone: small logos beside the names with the buttons under them, the pages' buttons under their titles, Reconnect on its own line, the linked jobs, and full-height Instructions,
- "copy id" on a company, an interview, a candidate, Settings and the account menu, each copying its own ID, and a long email on a candidate's page breaking before its @ on a phone instead of running off the screen,
- a company's billing: where the credits came from and went (a top-up, written as Paddle's web hook writes it, and a finished candidate's charge, opening their page) and the candidates whose credits are reserved, for owners and admins; a viewer has no billing tab, and its address sends them back to the interviews,
- a top-up opening the checkout the backend made in Paddle's overlay (skipped when Paddle's sandbox prices aren't in `.env`),
- a balance saying on hover that it's the current balance, in the company's header and on the billing page,
- the automatic top-up,
- an interview whose generation failed,
- the assistant: the welcome for the user's stage, an answer with a candidate row, voice through Chrome's fake microphone, the history, a reload in the middle of a chat, and a visitor who signs in from its sign-in card keeping their chat (answers stubbed: no OpenAI),
- the assistant's actions: one runs once its card is confirmed, asking to sign out signs out, and a pasted secret is removed from the chat and explained, with the page it belongs on,
- the assistant knowing the page (`p-assistant-page`, the real model, two messages; skipped without an OpenAI key, as in CI): on an interview's candidates tab, the message carries the page and its ids, "What can I do here?" reads the page's guide, and "Who's best here?" names that interview's candidate, not another interview's,
- the info buttons under the back arrow, explaining the companies list, an interview and a candidate, each opening the guide rounds serves for its page,
- the signed-in pages on a phone: lists and panels out to the screen's edges, actions on their own lines, dialogs across the screen with their buttons side by side, timed questions with nothing around them, and an invitation's rules before its start, out to the screen's edges, with the big start button,
- email settings: the defaults, each kind saved as it changes, the activity digest's box (all, none, some), and what the sign-in's email boxes turn on, at a first sign-in and a later one,
- unsubscribing: a user's activity digest link turns its four kinds off in Settings, and after a candidate's "Don't email me for <company>" link, the company's next invite to that address shows as undelivered. Links are signed with `EMAIL_LINK_SECRET` from `.env`.

**Cleanup.** Every throwaway address carries its run's tag (the run's container id, `RUN` in `helpers/users.ts`). After a run, `teardown.ts` deletes that run's throwaway accounts, and so their companies and data, and leftovers of stopped runs once they're over 6 hours old; another run's accounts are left alone while it may still be running, so runs at the same time don't delete each other's users (a deleted account is signed out at its next change). It fails if any of its own is left. It also runs before a run (a global setup), so a run starts without a stopped run's old leftovers.

Each run's traces and screenshots land in a folder of their own, `e2e_tests/signed-in/test-results/<run>` (screenshots under its `screenshots/`; the script prints the folder at the end), so runs at the same time don't empty each other's; folders older than a week are deleted at the next run.

```bash
./e2e_tests/signed-in.sh            # or: ./e2e_tests/signed-in.sh specs/b-candidate.spec.ts
```

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

Load tests with k6, in its Docker image, against the local stack only: never production, and not in CI.

- Scenarios: many candidates taking a test, owners on the dashboard, the public pages.
- Throwaway users, companies and tests from local templates, all deleted and counted afterwards.
- Settings, thresholds and results are in [e2e_tests/load/README.md](../e2e_tests/load/README.md).

```bash
./e2e_tests/load.sh candidates      # or: dashboard, public; VUS=20 ITERATIONS=2 ./e2e_tests/load.sh candidates
```

## Model and prompt evals

Model and prompt quality is tested offline with the prepared datasets, judge prompts and metrics in [evals/](../evals/README.md): question generation and its checks, and the assistant's page context (with it and without it, on throwaway data).

## CI

CI runs all of these except the end-to-end test, which needs an OpenAI key, and the load tests, but only for what changed.

- A service counts as changed when its folder or `packages/common` changed; the frontend, when `frontend/` did. A change to `ci.yml`, `scripts/ci_changes.sh` (which works this out) or `.python-version` counts as everything.
- A pull request compares with its base. `main` compares with the last commit CI passed on, so a failed run's changes are tested and built by the next one.
- Each changed part's unit tests run and its production image is built. A changed frontend also gets lint, types and the translations check (`pnpm check:messages`). On `main`, an unchanged part's image is the last passing commit's, tagged with the new commit too.
- Ruff and the file size check (`scripts/check_file_size.sh`: no hand-written file over 300 lines, CLAUDE.md rule 2) run on every change. So does the migration check (`scripts/check_migrations.py`): a new migration that builds an index without `CONCURRENTLY`, adds a foreign key or `CHECK` without `NOT VALID`, changes a column's type in place, sets `NOT NULL` without a validated check or renames, on a table that already exists, fails it (`.claude/rules/database.md`). Ruff and the frontend's ESLint also fail a function over complexity 15 (and, in Python, over 12 branches or 50 statements); tests and migrations are exempt in Python, the generated API types in the frontend.
- Terraform's format check, `terraform validate` (no credentials, no state, Terraform's version pinned) and TFLint (`infra/terraform/.tflint.hcl`: Terraform's recommended rules, and a type and description on every variable and output) run when `infra/terraform/` changed.
- ShellCheck checks every shell script on every change (`.shellcheckrc` also asks for `[[ ]]` in bash and quotes around every variable); when `.github/` changed, actionlint and zizmor check the workflows (tools pinned by version and checksum). Locally: `shellcheck $(git ls-files '*.sh')`, `actionlint` and `uvx zizmor@1.31.1 --offline .github`.
- The dependency audit (`.github/workflows/audit.yml`) runs on every change and every Monday: `pip-audit`, `pnpm audit --prod`, and gitleaks over the whole history (`.gitleaks.toml` allows tests' made-up keys and placeholders; mark another made-up value with a `gitleaks:allow` comment). On Mondays it also builds and scans every production image's OS packages with Trivy.
- It starts the whole stack for the smoke, integration, MCP, page and signed-in tests when any part changed, or `e2e_tests/`, `gateway/`, `database/`, `firebase/`, `scripts/`, `compose/` or `docker-compose.yml` did. A change to docs alone skips it.
- Its stack has no templates, so before the signed-in tests it adds a small English one (`e2e_tests/signed-in/seed/template.py`, no OpenAI).
- Its superadmin is a CI-only emulator account.
- On failure, the screenshots and traces are kept as the run's `signed-in-test-results` artifact.

When CI runs, and how releases follow it, is in [Deployment](deployment.md#cicd).
