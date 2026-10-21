# prepza-common

Code every prepza API service shares: sign-in, service tokens, logging, database and HTTP setup,
the outbox and Pub/Sub, notifications, who may do what in a company (asked of companies; a
company that's gone is no access), translated messages, a small in-memory cache, the admin zone's
stats counting and the limits several services read (`rate_limit.hit` counts uses, `rate_limit.spend`
adds up a cost such as tokens against a budget; a refusal is a 429 whose `Retry-After` gives the
seconds left in the limit's window, which `http.passed_on` keeps when it relays it; `rate_limit.recipient_key` is an address as the per-recipient email limit counts it, lowercased and without its `+tag`) and server-sent events (`sse`: the help chat's
and the assistant's answers, the bell's stream), secret tokens kept as their hashes (`tokens`: API
keys, AI apps' access), a visitor's address behind the load balancer (`client_ip`) and their country (`visitor_country`), requests to addresses someone gave
(`public_urls`: `public_address` lets only HTTPS to the public internet through, `pinned` connects
to that checked address: the api's web hooks, the assistant's AI app metadata documents) and
"select all that apply" questions (`multi_answer`: which questions are, how many of a draw are,
and the draw itself, by `MULTI_ANSWER_PERCENT`, a value in the admin zone's Controls).
OpenAI chat models: `llm.chat_model` builds them one way for every service (a temperature only at
reasoning effort `none`). It needs the package's `llm` extra (langchain-openai), so a service that
calls OpenAI depends on `prepza-common[llm]`; the others don't install it.
Tracing: `tracing` sends AI calls to Langfuse through its LangChain callback, only when
`LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` are set (`LANGFUSE_HOST`: the EU cloud unless set).
`traced_run(name, tags, seed)` makes every LangChain call inside it (LangGraph runs too) one trace,
tagged with ids only; `new_trace_id` and `traced(trace_id)` give the chats' answers theirs.
`answer_votes` mirrors the chats' thumbs up and down there as a score on the answer's trace. Both
need the `langfuse` extra: `prepza-common[llm,langfuse]` (generation, the assistant, rounds).
Limits: `limit_list.LIMITS` is every usage limit of ours (`limit_types.Limit`: its service, default,
unit, window, lowest and highest value, scope), and the plain values tuned beside them
(`counted=False`: nothing counts against them), and `limits.limit(redis, NAME)` its current value,
as a superadmin edited it in the admin zone (billing writes the `limits:values` hash; each instance
reads it at most every 30 seconds, and uses the default with Redis down). `limits.at_most` refuses
one more of a count (keys, members), `limits.question_seconds` gives a new test's seconds a
question by its level, and `limits.record_hit` records every refusal, ours or a
provider's, as a log line (`prepza_limit_hits`) and a `limit.hit` event billing stores;
`limit_schemas.BudgetOut` is a shared daily budget's use today, for the AI costs page.
AI costs: `ai_constants` holds the prices (`MODEL_PRICES`, `TRANSCRIPTION_PRICES`, the Batch API's
half) and every kind of AI call (`ACTIONS`), and `ai_usage.record` records one call with its tokens
and cost as an "AI used" log line (`prepza_ai_spend`) and an `ai.used` event billing stores;
`ai_usage.provider_refused` records OpenAI's rate limit and quota. `ai_cap` is the unpaid users'
daily AI spend cap (`AI_SPEND_UNPAID_DAY`): `refuse_if_capped` answers 503 once today's spend
reached it (with `Retry-After` to the next UTC day, `rate_limit.until_tomorrow`), and `add_unpaid` (billing) adds to it. Only `ai_usage` needs the `llm` extra.
Database: `db.database` builds a service's engine and sessions (its pool, and Postgres ending a
transaction left idle), `db.migration_engine` the migrations' one, and `db.delete_in_batches`
deletes old rows (retention, published events) `DELETE_BATCH` at a time, each batch its own
transaction.
Request bodies: `body_limit.BodyLimitMiddleware` refuses one over 1 MB (`MAX_BODY_BYTES`) with a
translated 413, counting a streamed body as it arrives; companies (report PDFs) and the assistant
(voice messages) pass larger limits.
Logs: `logging.configure_logging` writes one JSON line per entry in the fields Cloud Logging reads
(`severity`, `message`), and `RequestLogMiddleware` ties every line logged while serving a request
to its trace (`logging.googleapis.com/trace`, from the load balancer's `X-Cloud-Trace-Context`),
which `http.get_client` passes on to the services a request calls, so their lines join the same trace.
Each request's own line names its route's template (`/invites/{token}`), never the path, which can
carry a secret token; uvicorn's access log, which prints paths and visitors' addresses, is off.
Retries: `backoff.wait_seconds(first, attempt)` is the wait before a retry, doubling from `first`
with full jitter (the welcome credits, Langfuse votes).
Caching: `no_store.NoStoreMiddleware` marks every answer to a signed-in request `Cache-Control:
no-store`, unless its route set its own (a stream, a versioned logo).
Settings: `ServiceSettings` (`settings.py`) is the base of every service's `Settings`, with the
sign-in settings they all read (`FIREBASE_PROJECT_ID`, and `FIREBASE_AUTH_EMULATOR_HOST`, refused
unless the project is a `demo-` one). Each service's own settings live in its
`app/config/settings.py`, and it passes in what differs (its name, its database URL). Otherwise the
package reads only environment variables every service has: `BACKEND_SENTRY_DSN`,
`ENVIRONMENT`, `SENTRY_RELEASE` and `SENTRY_TRACES_SAMPLE_RATE`, `GOOGLE_CLOUD_PROJECT`,
`PUBSUB_EMULATOR_HOST` (locally), `ANALYTICS_SALT`, `SUPERADMIN_EMAILS`, `INVOKER_SERVICE_ACCOUNT`
and `INVOKER_AUDIENCE`, and the `<SERVICE>_SERVICE_SECRET` keys of the services it calls.

Services depend on it by path (see `[tool.uv.sources]` in each service's `pyproject.toml`). To
publish it instead, run `uv build` and `uv publish` here, then replace the path source with a
version requirement such as `prepza-common>=0.1`.
