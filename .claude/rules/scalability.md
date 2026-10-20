---
paths:
  - "services/**"
  - "packages/**"
  - "infra/**"
  - "compose/**"
  - "gateway/**"
  - "e2e_tests/load/**"
  - "frontend/next.config.ts"
---

# Scalability

Grow by adding instances, not by making one bigger or cleverer, and keep every shared resource
(Postgres connections, Redis commands, OpenAI tokens, queues) inside a stated budget. CLAUDE.md
wins on conflict; rule 4 decides between a practice and its complexity ("Not adopted" below).
Points other rule files already hold are only pointed at.

## Stateless services on Cloud Run

- An instance keeps nothing another request needs: no sessions, uploads or queues in memory or on
  disk; session affinity is best effort. Per-instance caches only hold what may be stale for their
  TTL (`prepza_common.memory_cache`); what every instance must agree on lives in Postgres or Redis.
- Each service's `min`, `max`, `concurrency`, `timeout`, CPU and memory are set in
  `infra/terraform/locals.tf` and explained there. `max` protects what the service uses (its
  database connections, OpenAI), never a guess at traffic.
- Concurrency: async IO-bound APIs take more requests than their pool has connections (they wait on
  IO, and Cloud Run scales at 60% of the limit); CPU-bound work (server rendering, PDFs) takes fewer.
  Change it only with a load test behind it.
- Size with Little's law: requests in flight = arrival rate × latency; instances needed = in flight
  ÷ concurrency, plus headroom for a cold start.
- Cold starts, billing per request and no work after the response: `.claude/rules/performance.md`
  (Delivery) and `.claude/rules/python-services.md` (FastAPI on Cloud Run).
- Long-held requests (the bell's stream, the assistant's turns) run on a service or limit of their
  own, so they never take the slots short requests and Pub/Sub's pushes need; each ends after a
  set time and the client reconnects.

## Postgres

- The connection budget, pool sizes and timeouts: `.claude/rules/database.md` (Connections;
  Sessions, transactions and queries). `statement_timeout` (`STATEMENT_TIMEOUT`, the shortest
  request timeout) is set on every service connection by `prepza_common.db`.
- Large deletes (retention, published events, processed-event notes) go `DELETE_BATCH` rows at a
  time, each batch its own transaction (`prepza_common.db.delete_in_batches`); the same for
  backfills. One statement never touches an unbounded number of rows.
- Every list a user or a job reads is bounded: a page (`MAX_PAGE_SIZE`), a batch, or a limit.
  OFFSET paging is fine inside one company; a list that can grow without end across tenants (logs,
  usage) pages by key (`WHERE (created_at, id) < (…)`).
- A new hot query is checked with `EXPLAIN (ANALYZE, BUFFERS)` on realistic data (writes inside
  `BEGIN … ROLLBACK`); Query Insights shows the slow ones in production.
- Before adding a read replica, cache or partition: an index, a smaller result, fewer queries.
  Replicas are asynchronous, so a read that must see the user's own write stays on the primary.
- Not adopted (yet): partitioning (until a table outgrows the instance's memory; retention deletes
  in batches until then), read replicas and PgBouncer (until the connection budget, not the query
  load, stops a service from scaling out; Cloud SQL's managed pooling needs Enterprise Plus).

## Redis (Upstash)

- Keys `area:kind:id`; every key that isn't a deliberate switch has a TTL, set in the same command
  (`SET … EX`, `SET … NX EX`) or the same transaction. No `KEYS`; no unbounded lists or sets.
- Pay per command: read shared values through the per-instance cache (limits: 30 s), pipeline
  what goes together, and never poll Redis in a loop without a wait.
- Spread a key every request writes (one per second for the LLM rate is fine; one per company or
  user is better than one global counter when both work).
- Upstash eviction stays off, so a rate limit is never evicted early; the database lives in the
  same region as the services.
- Redis pub/sub is a nudge, at most once: a listener that missed it reads the truth from Postgres
  (the bell re-reads on reconnect).
- Outage behaviour: `.claude/rules/python-services.md` (Redis).

## Events, queues and background work

- Pub/Sub for fan-out of domain events (outbox, push subscriptions, exponential retry, dead
  letters); Cloud Tasks for one job to one target with a concurrency cap (generation); Cloud
  Scheduler for periodic work. Nothing runs in-process after the response.
- Every handler is idempotent on the event's id and independent of order (rule 11); delivery is
  at least once. No exactly-once delivery or ordering keys (rule 4): they cost throughput and the
  handlers don't need them.
- A queue's concurrency (`max_concurrent_dispatches`) fits what its target can take: instances ×
  concurrency, and their database connections.
- A consumer that can't keep up answers 429/503 and Pub/Sub backs off; it never acks and drops.
  Backlog and dead letters alert (`.claude/rules/operations.md`).
- A scheduled job works in batches and stops before its deadline, leaving the rest to the next run
  (the outbox flush, bulk sends); it's safe to run twice at once.

## Web hooks and streams

- A received web hook is verified, recorded idempotently and answered within the provider's
  deadline (Paddle 5 s, Svix/Resend about 30 s); follow-up work goes through the outbox, not more
  synchronous calls before the answer. Signatures and ids: `.claude/rules/security.md`.
- Server-sent events: a heartbeat comment within 20 s, a cap per user, a maximum life, one shared
  Redis subscription per instance; the client reconnects with backoff. HTTP/2 at the load balancer
  lifts the browser's six connections per host.

## Caching

- Layers in order: the CDN for hashed and public static files (`.claude/rules/performance.md`,
  Delivery), `Cache-Control` on what may be shared, the per-instance cache for hot reads that may be
  stale for seconds, Redis only when instances must agree. Personal data never in a shared cache.
- Not adopted: a shared Next.js cache handler, stampede locks and early refresh (rule 4): the CDN
  coalesces requests, and the in-process TTLs are short and cheap to refill.

## AI workloads

- Calls are capped per job (`MAX_CONCURRENCY`) and across processes (the shared per-second rate in
  Redis, with jitter); work that can wait uses the Batch API; every call records its tokens and
  cost (`.claude/rules/ai.md`). Before scaling workers, check the OpenAI tier's TPM for the model.
- Chat and the assistant are not held behind bulk generation; spend caps fail closed
  (`.claude/rules/security.md`, Rate limiting).

## Timeouts and degradation

- Every call has a deadline shorter than its caller's: calls between services 15 s by default
  (`HTTP_TIMEOUT_SECONDS`), less where the callee is known to be fast; a request never waits
  longer than its Cloud Run timeout.
- Retries at one layer, with jittered backoff and a cap (`.claude/rules/python-services.md`).
- Overload sheds early: `429` with `Retry-After` for a caller over its limit, `503` with
  `Retry-After` for a daily cap or a paused feature; a non-essential part of a page (a count, a
  news title, the bell) is left out rather than failing the page.
- Not adopted: circuit breakers, retry budgets and criticality classes (rule 4).

## Load tests and capacity

- k6 in `e2e_tests/load`, only against the local stack or a test environment
  (`.claude/rules/testing-browser.md`). Capacity is measured with an open model (`RATE`: new
  candidates a minute), so a slow system can't slow the test down; the closed model checks a flow
  end to end.
- A change to a hot path (a candidate's answer, `start`, a list page) is load-tested before and
  after; numbers go to `e2e_tests/load/README.md`.
- Estimates, first bottlenecks and costs per size: `internal_docs/capacity-and-costs.md` and
  `internal_docs/scalability-best-practices.md` (local).

## Regions

- One region (`var.region`) with the CDN in front. Multi-region Cloud Run, cross-region replicas and
  data residency per customer wait for a latency target or a customer who needs them: each costs
  money and is the user's decision. GDPR doesn't require EU storage; transfers rest on the SCCs.

Research (local notes, git-ignored): `internal_docs/scalability-best-practices.md`.
