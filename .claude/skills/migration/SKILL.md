---
name: migration
description: Add an Alembic database migration to a service, run it locally and check the models match. Use when a model, index or constraint changes.
---

# Add a database migration

Each service with a database has its own Alembic history in `services/<svc>/migrations/versions/`.

## Write it

1. Find the last revision: `ls services/<svc>/migrations/versions | tail -1` (for example
   `0013_history_index.py`).
2. Add the next one by hand, `00NN_<what_it_does>.py`, following the existing files:

   ```python
   """<what changes and why, in a sentence or two>

   Revision ID: 0014
   Revises: 0013
   Create Date: <today>
   """

   from alembic import op

   revision = "0014"
   down_revision = "0013"
   branch_labels = None
   depends_on = None


   def upgrade() -> None:
       ...


   def downgrade() -> None:
       ...
   ```

3. Keep it additive where you can: a rollback redeploys older code on the newer schema
   (`infra/README.md`, Rolling back), so don't drop or rename what running code still reads.
4. Follow `.claude/rules/database.md`, Migrations without downtime: an index on an existing
   table is built concurrently inside `autocommit_block()`; a new foreign key or `CHECK` on one
   is added `NOT VALID` and validated in a later migration; no column type changes in place;
   a short `lock_timeout`.

   ```python
   with op.get_context().autocommit_block():
       op.create_index("ix_t_col", "t", ["col"], postgresql_concurrently=True)
   ```

   `scripts/check_migrations.py` (run in CI) fails on what this rules out; a statement the rule
   allows anyway (a table known to hold a few rows) carries `# migration-check: <why>`.

5. Change the model in `app/models/` to match: column types, `server_default`, `ondelete` and an
   index on every new foreign key as the database rule says.

## Run and check

```bash
/opt/homebrew/bin/docker-compose run --rm --no-deps <svc>-migrate
/opt/homebrew/bin/docker-compose run --rm --no-deps <svc>-migrate \
  sh -c 'cd /services/<svc> && .venv/bin/alembic check'
scripts/integration.sh <svc>
```

`alembic check` reports nothing on a freshly migrated database, and each service's
`tests/integration/test_migrations.py` runs it there: a model and its migration change together.
The same file asserts that `prepza_common.schema_rules.problems` finds nothing: a rule of
`.claude/rules/database.md` it checks can't be broken by a new table.
Objects managed outside the models are skipped in `migrations/env.py` (library's
`topics.embedding`, notifications' `legal_notices`). On the dev database it can also list tables
an old local setup left behind; those aren't yours to drop.

## Report

Name the migration and remind the user it must run in production with the deploy
(the deploy workflow's **Run migrations**).
