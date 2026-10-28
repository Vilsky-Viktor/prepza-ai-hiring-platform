---
paths:
  - "services/**"
  - "packages/**"
  - "infra/**"
  - "compose/**"
  - "gateway/**"
  - "database/**"
  - "docker-compose.yml"
  - ".github/workflows/**"
---

# Microservices

What goes in which service, how services depend on each other, and when to split, merge or move.
CLAUDE.md wins on conflict: rule 4 keeps out every layer the need doesn't require ("Not adopted"),
rule 10 says a domain several services reimplement gets its own service. Calls, retries and
timeouts: `python-services.md`; scaling: `scalability.md`; tables: `database.md`.

## 1. Single responsibility

- A service owns one business capability. Its README's first sentence names it; work that
  doesn't fit that sentence belongs to another service, or to a new one by the checklist below.
- Things that change for the same reason live in one service; a feature that has to change three
  services is a sign of a wrong boundary, not of a need for a fourth.
- Owners today: companies (companies, members, interviews, candidates' invites, results), rounds
  (candidates' sessions and answers, practice rounds), site (the public site's content: the FAQ,
  page guides, guide articles, legal texts), library (the question bank), generation
  (AI drafting and checking), billing (credits, payments, AI costs, limits), notifications
  (email, Slack, the bell), ats (ATS connections), api (the public API, web hooks), assistant
  (Mira, the help chat for visitors, and MCP), accounts (users' accounts: settings, email
  settings, accepted terms, deleting and downloading an account). New code goes to its owner; code found in the
  wrong service moves there.

## 2. Database per service

- Each service has its own database and Postgres user owning only it (`db_roles`); no service
  reads or writes another's tables, no foreign key crosses services, no table is shared.
- Another service's data comes through its API (batched by `ids`, never one call per row) or
  from its events into a local copy holding only the fields needed, updated by those events.
- A reference to another service's row is a plain `uuid` column; its removal reaches the holder
  as an event (`company.deleted`, `interview.deleted`), handled idempotently.
- A change across services is a saga: each step a local transaction with its event in the
  outbox, a compensation for a step that can fail after others committed. No two-phase commit.
- One owner per fact: a value two services need (a legal version, a limit) is written by one
  and read by the rest through its API, its event or `prepza_common` constants, never kept twice.

## 3. Independent deployability

- Each service builds its own image, runs its own migrations and can be rolled back alone.
  Releases deploy every service at one version (the release train stays: one developer);
  nothing may require two services to switch at the same moment.
- Contracts change backward compatibly for at least one release: add fields, routes and event
  types first; switch the callers; remove the old only when no running version uses it. Never
  rename or drop a field, route or event type in the release that stops using it.
- Consumers ignore fields and event types they don't know (tolerant reader); a producer never
  changes what an existing field means.

## 4. Loose coupling and high cohesion

- No content coupling (reaching into another's data or Redis keys), no pass-through coupling
  (a service forwarding a call only to add a check the callee could make itself).
- Shared mutable state in Redis has one writer per key family (switches, limits), documented
  where it's written; others only read it.
- Synchronous chains stay short: a user's request waits on at most two services below the one
  it reached. Avoid cycles of synchronous calls; when two services call each other for one
  flow, one direction becomes an event.
- A hot path (a candidate answering, a page's first paint) depends synchronously on as few
  services as possible; what it needs from others is loaded once at its start.

## 5. API-driven communication (REST, gRPC or events; no shared internal code)

- Services talk only through HTTP routes (REST, JSON) and Pub/Sub events; never by importing
  another service's code, reading its files at run time or sharing its database.
- Routes other services call are `/internal/...`, in the service's OpenAPI, signed with a
  service token and allowed by `run.invoker` on that callee only (`locals.tf` `calls`).
- Every event type has one producer, a past-tense name (`interview.deleted`), a Pydantic payload
  model and a line in `docs/architecture.md`'s table of consumers. Facts every holder reacts to
  go as events (choreography); a sequence where a step may refuse and the starter must know runs
  as calls from one owner (orchestration).
- `prepza_common` holds generic code and published contracts: event names and payload models,
  error codes, thin clients of one route shared by several callers. Never a business rule,
  a decision or a table of one service (`python-services.md`, Shared library).

## 6. Failure isolation and resilience (circuit breakers, retries, fallbacks)

- Timeouts on every call, one retry layer with jittered backoff, idempotency keys, 429/503 with
  `Retry-After`: `python-services.md` and `scalability.md`.
- Work that can wait goes through Pub/Sub or Cloud Tasks (retries, dead letters), so a callee's
  outage delays it instead of failing the user.
- Fallbacks: a non-essential part of a page is left out when its service fails; a service keeps
  working, degraded, while Redis is down.
- Bulkheads: work with a different load (long streams, AI jobs) runs on a Cloud Run service of
  its own, from the same image when only the load differs (`generation-worker`,
  `notifications-stream`), so it never takes the slots of short requests.
- Circuit breakers: not adopted (rule 4); timeouts and queues absorb today's failures. Add one
  only when a callee's outage is measured filling a caller's slots.

## 7. Centralized observability (tracing, correlation ids, logging)

- The Cloud trace id is the correlation id; there is no second one. Every log line carries it
  (`prepza_common.observability.logging`), every call passes it on (`prepza_common.http.http`),
  and every event carries it from the outbox row as a message attribute, so a consumer's lines
  join the action that caused them.
- Logs go to stdout as one-line JSON for Cloud Logging; errors to Sentry tagged with the
  service; `/health` and `/ready` per service; alerts and SLOs in `operations.md`.
- Distributed tracing spans (OpenTelemetry, Cloud Trace): not adopted yet; add them when a slow
  path can't be found from the joined logs.

## 8. DevOps and automation (CI/CD, containers, orchestration)

- Every service is a container built from its own Dockerfile, tested and built in CI only when
  it or `packages/common` changed, deployed by the pipeline with its migrations and smoke test.
- Twelve-factor: config from the environment, backing services by URL, stateless and disposable
  processes, dev/prod parity (compose mirrors Terraform), admin work as one-off jobs.
- Orchestration is Cloud Run; no Kubernetes or service mesh (rule 4).
- Adding a service updates, in the same change: `infra/terraform/locals.tf` (services, calls,
  keys, secrets, the connection budget), `consumes` for its events, `database/init.sql`,
  `compose/`, `gateway/nginx.conf`, the CI matrix, `deploy.yml` (`SERVICES`, migrations), the
  root README and `docs/architecture.md`. Removing one undoes each.

## How to decide a split, merge or move

Answer in order; stop at the first that settles it.

1. **Is it in the wrong service?** Move it to the capability that owns it. Moving between
   existing services comes before any new service.
2. **Does only the load differ** (streams, AI jobs, bulk sends)? Split the deployment: the same
   image as another Cloud Run service with its own limits. No new code base or database.
3. **Is it a capability of its own?** It has its own data, few reasons to change together with
   its neighbour, and no transaction it must share with it. If it shares a transaction or most
   changes touch both, keep it together: a split makes a distributed monolith.
4. **Is a force for splitting real now?** A different scaling or failure profile, a secret or
   compliance boundary to narrow, a domain several services reimplement (rule 10), or a
   synchronous dependency that puts a hot path at risk. File size and "it might grow" are not.
5. **Is the cost worth it?** Each service adds a Cloud Run service, a database and user, a
   connection share, a deploy step, a network hop's latency and failures, and the list in 8.
   Writing the case down (benefit, cost, risk, migration) comes before any code.
6. **Merge** two services that change together for most features or call each other on every
   request.

Pre-launch, moving data is cheapest; scaling spend (more instances, a bigger database) waits
until 20–30 paying companies.

## Not adopted (rule 4)

gRPC, a service mesh, Kubernetes, a repo or version per service, an event schema registry, a
database instance per service, circuit breaker libraries and tracing SDKs: each waits for the
measured need named above.

Research (local notes, git-ignored): `internal_docs/best-practices/microservices.md`; the review
of each service: `internal_docs/plans/microservices-split.md`.
