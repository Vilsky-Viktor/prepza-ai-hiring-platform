---
paths:
  - "services/*/app/models/**"
  - "services/*/app/storage/**"
  - "services/*/migrations/**"
  - "services/*/alembic.ini"
  - "packages/common/src/prepza_common/db/db.py"
---

# Database (Postgres, SQLAlchemy 2.0 async, Alembic)

One Cloud SQL instance, a database per service. Adding a migration: the `migration` skill.

## Columns

- Timestamps are `timestamptz` (`DateTime(timezone=True)`); JSON documents `jsonb`; text is
  `text`, or `varchar(n)` only where the limit is a real rule; never `char(n)` or `money`.
- Money is an integer in minor units (credits, cents); fractional amounts (AI spend in fractions
  of a cent) are `numeric`; never a float. Payments and the credit ledger:
  `.claude/rules/payments.md`.
- Ids that leave the service are `uuid`, the same type in every service (a `company_id` is never
  `uuid` in one and `varchar` in another). New integer keys use `Identity()`, not `serial`.
- `created_at` has `server_default=func.now()`, so rows written outside the ORM get it too.
- A closed set of values is a string column with a `CHECK (col IN (...))`, not a native `ENUM`
  (values can't be removed from one), built from its enum (`prepza_common.db.db.one_of`); a value
  added to the enum changes the CHECK in a migration (`test_migrations.py` compares them).
- Every `Base` sets `MetaData(naming_convention=NAMING_CONVENTION)` (`prepza_common.config.constants`:
  Postgres' own names for `uq`, `fk`, `pk`, so existing names stay) so migrations can drop and
  rename constraints by name; a `CHECK` is named where it's made (`ck_<table>_<what>`).

## Constraints and indexes

- The database enforces what the code relies on: `NOT NULL`, `UNIQUE`, foreign keys and `CHECK`
  (e.g. `reserved >= 0`). App validation gives the friendly message; the constraint stops races
  and other writers.
- Every foreign key states `ondelete` (`CASCADE`, `SET NULL` or `RESTRICT`) on purpose, and its
  column is indexed (alone or as the first column of a composite index).
- Index what queries filter on: composite indexes in the query's column order, partial indexes
  for a hot subset (unpublished outbox rows), expression indexes (`lower(email)`).
- "Only one of X" is a unique constraint written with `INSERT ... ON CONFLICT`; "at most N" takes
  a row lock or `pg_advisory_xact_lock` before counting. Never read-then-insert unguarded
  (rule 11).

## Tenancy and deletion

- Every tenant-owned row carries `company_id`. A route reaches tenant data through one access
  check (`interview_for`, `candidate_for`, `require_company`); new repositories that serve users
  take `company_id` and filter on it. No Postgres row-level security (rule 4).
- Hard delete by default; no soft-delete flags. What must be kept goes to an audit or archive
  table; an erasure request removes the person's data without undue delay.

## Migrations without downtime

Migrations run before the new version deploys, while the old one serves traffic, and a rollback
runs older code on the newer schema.

- Expand, then contract: add columns, tables and indexes first; switch the code; drop the old
  only once no running version reads it. Never rename or drop in the same release that stops
  using it; never change a column's type in place (add a column, backfill in batches, switch).
- Migrations run with a short `lock_timeout` (about 5 s) and a `statement_timeout`, so a lock
  queued behind a long query fails fast instead of blocking every query on the table.
- An index on an existing table is built `CONCURRENTLY` (`postgresql_concurrently=True` inside
  `op.get_context().autocommit_block()`); a failed build leaves an `INVALID` index to drop.
- A new foreign key or `CHECK` on an existing table is added `NOT VALID`, then validated in a
  later step. `SET NOT NULL` on a big table goes through a validated `CHECK (col IS NOT NULL)`.
- Adding a column with a constant default is fine (instant).
- Read every migration: autogenerate misses renames and some constraint and type changes;
  `alembic check` must show no new drift for the changed tables.

## Sessions, transactions and queries

- One `AsyncSession` per unit of work, opened by the service and passed to the repositories
  (`python-services.md`), never shared between concurrent tasks; `expire_on_commit=False`
  (`prepza_common.db.db`).
- A transaction covers exactly what must succeed together; no call to another service or a model
  while it's open (it holds locks and a pooled connection). Events leave through the outbox in
  the same transaction.
- No query per loop item: load related rows with `selectinload` (`joinedload` for many-to-one)
  and batch lookups with `WHERE id IN (...)`.
- Server-side limits: `idle_in_transaction_session_timeout` frees connections a hung request
  left open; a `statement_timeout` stops runaway queries, raised with `SET LOCAL` only for jobs
  that need longer.

## Connections

- Σ(max instances × (`pool_size` + `max_overflow`)) over all services, plus the deploy overlap,
  stays under `max_connections` minus a reserve; Terraform checks it. A change to a service's
  `max` instances or pool updates that budget.
- `max_connections` fits the instance tier's memory; `pool_recycle` replaces old connections.
- Large deletes and backfills go in batches; paging, replicas and partitioning:
  `.claude/rules/scalability.md`.

Research (local notes, git-ignored): `internal_docs/best-practices/database.md`.
