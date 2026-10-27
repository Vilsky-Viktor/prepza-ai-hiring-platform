from logging.config import fileConfig

from alembic import context
from langgraph.checkpoint.postgres import PostgresSaver
from prepza_common.db.db import migration_engine

import app.models.batch_work  # registers the tables on Base.metadata
import app.models.generation
import app.models.key_checks
import app.models.outbox
import app.models.patterns  # noqa: F401
from app.config.settings import settings
from app.models.base import Base

fileConfig(context.config.config_file_name)

# LangGraph's checkpointer creates and migrates these itself (PostgresSaver.setup(), below), so
# they have no models: autogenerate leaves them alone.
CHECKPOINT_TABLES = {
    "checkpoints",
    "checkpoint_blobs",
    "checkpoint_writes",
    "checkpoint_migrations",
}


def include_name(name, type_, parent_names):
    """Skips LangGraph's checkpoint tables (see CHECKPOINT_TABLES)."""

    return not (type_ == "table" and name in CHECKPOINT_TABLES)


engine = migration_engine(settings.database_url)

with engine.connect() as connection:
    context.configure(
        connection=connection, target_metadata=Base.metadata, include_name=include_name
    )

    with context.begin_transaction():
        context.run_migrations()

# LangGraph's own tables are created and migrated here, with ours, before a release serves: not
# at each start of the worker, which would run DDL on every cold start.
with PostgresSaver.from_conn_string(settings.database_url) as saver:
    saver.setup()
