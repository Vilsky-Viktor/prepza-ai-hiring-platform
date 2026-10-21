from logging.config import fileConfig

from alembic import context
from prepza_common.db import migration_engine

import app.models.emails  # registers the tables on Base.metadata
import app.models.events
import app.models.feedback
import app.models.legal
import app.models.news
import app.models.outbox
import app.models.quality
import app.models.sets  # noqa: F401
from app.config.settings import settings
from app.models.base import Base

fileConfig(context.config.config_file_name)


def include_object(object, name, type_, reflected, compare_to):
    """topics.embedding is a pgvector column (migration 0011), read and written with SQL
    (storage/reuse.py) rather than mapped: autogenerate leaves it alone."""

    return not (type_ == "column" and name == "embedding" and object.table.name == "topics")


engine = migration_engine(settings.database_url)

with engine.connect() as connection:
    context.configure(
        connection=connection, target_metadata=Base.metadata, include_object=include_object
    )

    with context.begin_transaction():
        context.run_migrations()
