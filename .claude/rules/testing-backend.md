---
paths:
  - "services/*/tests/**"
  - "packages/common/tests/**"
  - "services/*/migrations/env.py"
---

# Python tests

Shared test rules are in `testing.md`; CLAUDE.md wins on any conflict.

## pytest

- Setup and teardown together in fixtures (`yield`); a fixture can return a factory that
  cleans up what it made; expensive fixtures get a scope on purpose.
- Tables of cases with `@pytest.mark.parametrize`, not loops or copied tests.
- Time and randomness are deterministic: pass times in (most storage functions take
  `before`/`since`) rather than reading `datetime.now` inside the code under test.
- Not adopted (rule 4, no test plugins): pytest-asyncio (coroutines run with `asyncio.run`),
  pytest-randomly, pytest-rerunfailures, time-machine/freezegun, pytest-alembic.

## FastAPI

- Replace auth, sessions and clients with `app.dependency_overrides`, cleared in teardown.
- Async tests use `httpx.AsyncClient(transport=ASGITransport(app))`; it skips lifespan, so a
  test that needs start-up uses `with TestClient(app)`.

## Databases and migrations

- Real Postgres (and pgvector) through `scripts/integration.sh`, never SQLite.
- Isolation: each service's `_test` database is shared per session and never rolled back, so
  each test makes its own rows with fresh uuids and never counts or lists a whole table.
- Each service's `test_migrations.py` checks that its tables match its migrations; anything
  outside the models is skipped in `migrations/env.py` with the reason.
- Migration checks: one head, base→head applies, models match the DDL. Autogenerate misses
  renames and some types, so a generated migration is still read (the `migration` skill).
- Not adopted: migration downgrades. A rollback redeploys older code on the newer, additive
  schema (`deploy.yml`), so no test runs a downgrade.
- Race tests prove the race: the second transaction is seen waiting on the lock (poll
  `pg_locks`, or a barrier) before the first commits. A sleep only hopes so and passes on a
  slow machine without racing.

## Redis, Pub/Sub and events

- Real Redis in medium tests, not mocks.
- Pub/Sub runs on the emulator (`PUBSUB_EMULATOR_HOST`); it lacks IAM, schemas and some
  ordering features, so those aren't tested against it.
- Delivery is at least once (rule 11): test that a duplicate changes nothing twice, that
  out-of-order and replayed sequences are handled, and what happens after the last retry
  (dead letter).
- Wait for the event to arrive or the row to change; never sleep for it.

Research (local notes, git-ignored): `internal_docs/best-practices/testing.md`.
