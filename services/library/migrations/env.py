from logging.config import fileConfig

from alembic import context
from prepza_common.db.db import migration_engine

import library.models.emails  # registers the tables on Base.metadata
import library.models.erasures
import library.models.events
import library.models.feedback
import library.models.legal
import library.models.news
import library.models.outbox
import library.models.quality
import library.models.sets  # noqa: F401
from library.config import settings
from library.models.base import Base

fileConfig(context.config.config_file_name)


def include_object(object, name, type_, reflected, compare_to):
    """topics.embedding is a pgvector column (migration 0011), read and written with SQL
    (repositories/reuse.py) rather than mapped: autogenerate leaves it alone."""

    return not (type_ == "column" and name == "embedding" and object.table.name == "topics")


engine = migration_engine(settings.database_url)

with engine.connect() as connection:
    context.configure(
        connection=connection, target_metadata=Base.metadata, include_object=include_object
    )

    with context.begin_transaction():
        context.run_migrations()
