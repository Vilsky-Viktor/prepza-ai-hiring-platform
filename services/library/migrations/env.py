from logging.config import fileConfig

from alembic import context
from prepza_common.db.db import migration_engine

import library.models.bank  # registers the tables on Base.metadata
import library.models.events
import library.models.feedback
import library.models.outbox
import library.models.quality
import library.models.sets  # noqa: F401
from library.config import settings
from library.models.base import Base

fileConfig(context.config.config_file_name)


def include_object(object, name, type_, reflected, compare_to):
    """topics.embedding and bank_questions.embedding are pgvector columns (migrations 0011 and
    0039), read and written with SQL (repositories/reuse.py, repositories/bank.py) rather than
    mapped: autogenerate leaves them alone."""
    return not (
        type_ == "column"
        and name == "embedding"
        and object.table.name in {"topics", "bank_questions"}
    )


engine = migration_engine(settings.database_url)

with engine.connect() as connection:
    context.configure(
        connection=connection, target_metadata=Base.metadata, include_object=include_object
    )

    with context.begin_transaction():
        context.run_migrations()
