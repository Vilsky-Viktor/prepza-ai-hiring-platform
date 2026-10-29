# Load tests

[k6](https://k6.io) scripts, run in k6's Docker image (`grafana/k6:2.3.0`; nothing to install) against the running local stack. k6 joins the stack's Docker network and calls the gateway by name on its inner port (`http://gateway:8081`, which skips the per-IP limit every visitor gets, as all of k6's users share one address), so it loads the same nginx, services, Postgres, Redis and Pub/Sub emulator the app uses.

Each Monday, `.github/workflows/load.yml` runs `public`, `candidates` and `dashboard` with the defaults on a stack started on the GitHub runner; a crossed threshold or a leftover fails it.

**Never run this against production.** The signed-in scenarios make users in the Firebase Auth emulator, so they run only locally; `load.sh` refuses them for any other host. Only `public` may be pointed at a test environment, with `BASE_URL=... e2e_tests/load.sh public --i-mean-it`.

- [Running](#running)
- [Scenarios](#scenarios)
- [Thresholds](#thresholds)
- [Clean-up](#clean-up)
- [Results](#results)

## Running

```bash
e2e_tests/load.sh candidates          # many candidates taking a test at once
e2e_tests/load.sh dashboard           # company owners on their dashboard
e2e_tests/load.sh public              # signed-out pages and the public API
e2e_tests/load.sh clean               # delete what an interrupted run left behind

VUS=20 ITERATIONS=2 THINK_SECONDS=3 e2e_tests/load.sh candidates
RATE=10 DURATION=3m e2e_tests/load.sh candidates   # capacity: 10 new candidates a minute
PAGES=0 VUS=20 e2e_tests/load.sh public    # the public API only, without the frontend
```

| Setting | Default | Meaning |
|---|---|---|
| `VUS` | 5 | Users at once |
| `RATE` | 0 | `candidates`: new candidates a minute for `DURATION`, however fast the stack answers (an open model, for finding capacity; a run fails when arrivals are dropped). 0: `VUS` take `ITERATIONS` turns |
| `DURATION` | 1m | How long `dashboard` and `public` run, and `candidates` with `RATE` |
| `ITERATIONS` | 1 | `candidates`: tests each user takes, one after the other (each as a new candidate) |
| `THINK_SECONDS` | 1 | Pause between two actions: reading a question, looking at a page |
| `COMPANIES` | 3 | `dashboard`: throwaway companies, each with 3 finished candidates |
| `TEMPLATE_ID` | smallest usable | The local template tests are made from (never generated: no OpenAI) |
| `PAGES` | 1 | `public`: 0 leaves the frontend's pages out |
| `BASE_URL` | `http://gateway:8081` | Only `public` may use another host, with `--i-mean-it` |

The defaults are modest: the local Docker VM has little free memory, and the frontend's dev server (3 GB and more) is the first thing to run out. Raise `VUS` a step at a time and watch `docker stats`. Run it with nothing else using the stack: with browser tests on the same VM, latency doubles and even the default run crosses the thresholds (seen: 5 candidates, `start` p95 1.2 s, `answer` 1.3 s).

## Scenarios

- **candidates.** Setup makes throwaway owners, each with a company, a test copied from a local template and the test's shareable link on. A company's welcome credits pay for 3 candidates, so there's one owner and company per 3 candidates. Each iteration is a new candidate: signs up in the emulator (verified email), opens the link (`link`), starts (`start`) and answers as the interview page does, `step` then `answer`, until the step says the interview is done. Answers are random. The link starts a candidate exactly as an email invite does (same sessions, same credits held), without emailing anyone or reading invite codes from the database.
- **dashboard.** Setup makes `COMPANIES` companies, each with a test 3 candidates have finished. Each iteration an owner opens their companies (`companies`), the tests list (`interviews`), a test (`interview`), its candidates best grade first (`candidates`), filtered by a status or result (`filtered`, every filter in turn), a candidate's scorecard (`scorecard`) and the candidates report (`report`).
- **public.** A signed-out visitor opens the home, pricing, FAQ, documents and practice pages, and the public API those read: the price catalog (`catalog`), the practice tests (`templates`) and the FAQ (`help_faq`). The first request of each page, which makes the dev server compile it, is made in setup and not measured.

Sign-ups, setup and clean-up calls carry no endpoint name and count towards no threshold.

## Thresholds

A run fails (k6 exits non-zero) when any is crossed:

| What | Local threshold |
|---|---|
| p95 of each API endpoint above | under 500 ms |
| p95 of each page | under 2 s |
| Failed requests (4xx/5xx, timeouts) | under 1% |
| `candidates`: interviews finished | over 99% |

These are for the local stack: one uvicorn process per service in reload mode, Next's dev server, the Pub/Sub emulator, all in one Docker VM on a laptop, often shared with other test runs. They catch a regression, not a capacity.

Targets for production (Cloud Run, a production frontend build): p95 under 300 ms and p99 under 1 s for `step` and `answer`, under 500 ms for the dashboard's endpoints and `start`, under 1 s for server-rendered pages; errors under 0.1%. Check them at 50, 200 and 500 users at once on a test environment with the `public` scenario (the signed-in ones run only locally); there's no test environment yet, so that needs one first.

## Clean-up

After every `candidates` and `dashboard` run, and on `clean`, `load.sh`:

1. lists the throwaway companies and users still in the databases (`leftovers.sh ids`);
2. deletes every throwaway account (`clean.js`) the way a user does in settings (`DELETE /api/accounts/me`), candidates first, which also deletes the companies they alone own;
3. counts the rows left that hold one of those ids in companies, members, tests, candidates, audit events, rounds' sections, library's sets, billing's wallets and holds, ATS connections and users' and companies' notifications (`leftovers.sh count`), and fails when any is.

Only load runs' rows ever match: companies named `Load <run> <n>`, owners at `load-<run>-owner-<n>@example.com`, candidates at `delivered+load-<run>-candidate-<n>@resend.dev` (Resend's test domain, which delivers to nobody). The users' own local records are never touched.

## Results

First local runs of 2026-10-06, before the optimisations below, on an Apple Silicon laptop, Docker VM with 8 CPUs and 7.7 GB, about 2 GB free, other test runs (Playwright, integration tests) on the same VM at the same time. The numbers vary by 2x between runs; read them as orders of magnitude.

| Scenario | Load | Requests | p95 per endpoint | Errors | Thresholds |
|---|---|---|---|---|---|
| candidates | 1 user, no pause (baseline) | one candidate's | link 11 ms, start 99 ms, step 40 ms, answer 47 ms | 0% | pass |
| candidates | 10 users × 3 candidates, no pause | 690 in about 12 s (about 55 a second) | link 183 ms, start 698 ms, step 365 ms, answer 335 ms | 0% | fail: start |
| candidates | 20 users × 2 candidates, 3 s pause (40 candidates, 14 companies) | 920 in about 70 s (about 13 a second) | link 416–713 ms, start 1.2–1.6 s, step 534–808 ms, answer 843–898 ms | 0% | fail: start, step, answer |
| dashboard | 1 user, 30 s, 0.5 s pause (baseline) | — | scorecard 198 ms, every other under 60 ms | 0% | pass |
| dashboard | 10 users, 1 min, 1 s pause | 977 | companies 179 ms, interviews 190 ms, interview 767 ms, candidates 155 ms, filtered 130 ms, scorecard 606 ms, report 637 ms | 0% | fail: interview, scorecard, report |
| public, API only | 20 users, 1 min, 1 s pause | 3,312 (about 55 a second) | catalog 42 ms, help_faq 16 ms, templates 372 ms | 0% | pass |
| public, with pages | 3 users, 1 min, 1 s pause | 192 | home 3.5 s, pricing 9.2 s, faq 496 ms, documents 462 ms, practice 436 ms; API under 100 ms | 0% | fail: home, pricing |

What the runs showed:

- **Nothing failed**: no errors and every candidate finished, at every load tried; only latency grew. The frontend's dev server didn't run out of memory at 3 users (it stayed at about 3.3 GB).
- **`rounds` and `library` are the busy services.** At 20 candidates `rounds` and `library` each ran at a full core (one process each) and the Pub/Sub emulator at two. Each `answer` publishes its event to Pub/Sub inside the request, and the event makes `library` update the question's statistics. Locally every service's subscription gets every event (in production each filters to its own types), which adds to it.
- **`start` is the slowest candidate call**: it reads the test's questions from `library` to pick the candidate's, then creates the sections in `rounds`, for every candidate.
- **`scorecard` is the heaviest dashboard call**: the full review of every answered question from `rounds`, an analytics event published inside the request, an audit row.
- **`report` reads every candidate of a test, unpaged**, and their scores from `rounds` in one call. With 3 candidates a company here (what the welcome credits pay for) it's fast alone; a test with hundreds of candidates was not tried.
- **Pages:** the dev server compiles and renders on request and recompiles when files change, so its seconds-long spikes say nothing about production; measure pages against a production build (`next start`) or staging.

### Optimisations

Measured on 2026-10-06 by switching each change off and on between runs of the same settings, several pairs in a row, on the same VM (at times shared with browser tests, which doubled every number, including endpoints nothing changed). Numbers are p95 (median), before → after.

| Change | Endpoint | 10 users × 3, no pause, shared VM | 10 users × 3, no pause, quiet VM | 20 users × 2, 3 s pause, quiet VM |
|---|---|---|---|---|
| `step` reads the candidate's sections once (4 database transactions instead of about 7) and no longer loads integrity signals, which only the scorecard shows | `step` | 714 / 584 ms → 477 / 271 ms (249 / 236 → 156 / 100 ms) | 321 / 176 ms → 227 / 128 ms (141 / 99 → 104 / 56 ms) | 220 / 321 ms → 394 / 235 ms (59 / 37 → 36 / 29 ms) |
| The same; `answer` also loads no signals | `answer` | 503 / 728 ms → 506 ms / 1.8 s (257 / 217 → 205 / 142 ms) | 242 / 152 ms → 194 / 152 ms (122 / 84 → 98 / 77 ms) | 179 / 363 ms → 413 / 254 ms (54 / 33 → 50 / 47 ms) |
| A test's page keeps the test's topics from `library` for 30 s (`SET_CACHE_SECONDS` in companies) | `interview` (10 owners, 1 min, 1 s pause) | 732 / 418 ms → 260 / 80 ms (93 / 300 → 17 / 14 ms) | 98 ms → 59 ms (59 → 9 ms) | — |
| The scorecard asks `rounds` for the review and the scores at once, and writes the audit row while the funnel event is published | `scorecard` (same) | 629 / 473 ms → 542 / 225 ms (211 / 280 → 124 / 65 ms) | 139 ms → 163 ms (93 → 50 ms) | — |
| `library` re-reviews a question's quality after an answer only once it has been shown `MIN_ANSWERS` (30) times: before that an answer can't change its flag | `library`, per `answer.recorded` event (150 events, real database) | — | 7.5 ms → 2.2 ms | — |

Medians fell for every change; the p95s moved with whatever else the VM was doing (a single slow request is the p95 of a 30-candidate run). Tried and not kept: keeping the test's questions in memory for `start`, which showed no gain locally (the load test's tests are small and each has 3 candidates).

Compared with `internal_docs/operations/capacity-and-costs.md` (kept out of the repo; an estimate of 100–300 requests a second per service): locally the candidate flow (mostly `rounds`) peaked at about 55 requests a second, with `step` and `answer` at a p95 around 350 ms before the optimisations above, while `rounds` and `library` each used a full core and Postgres under 70% of one, on a shared VM in reload mode. It's a floor, not the production figure, but it says the services' single processes, not the database, are the first limit, and that `rounds` and `library` are the ones to scale or optimise first.
