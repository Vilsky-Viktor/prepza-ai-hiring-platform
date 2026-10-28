from logging.config import fileConfig

from alembic import context
from prepza_common.db.db import migration_engine

import library.models.events  # registers the tables on Base.metadata
import library.models.feedback
import library.models.news
import library.models.outbox
import library.models.quality
import library.models.sets  # noqa: F401
from library.config import settings
from library.models.base import Base

fileConfig(context.config.config_file_name)


# Users' email settings, their consent log, accepted terms and recent erasures moved to the
# accounts service; library no longer reads these tables, which go in the release after the move
# (expand, then contract: the version before still reads them while this one deploys).
MOVED_TO_ACCOUNTS = {"email_preferences", "email_consents", "terms_acceptances", "erasures"}


def include_object(object, name, type_, reflected, compare_to):
    """topics.embedding is a pgvector column (migration 0011), read and written with SQL
    (repositories/reuse.py) rather than mapped: autogenerate leaves it alone. The tables moved to
    accounts aren't library's models any more, until a migration drops them."""
    if type_ == "table" and name in MOVED_TO_ACCOUNTS:
        return False

    if type_ in ("index", "column", "unique_constraint") and object.table.name in MOVED_TO_ACCOUNTS:
        return False

    return not (type_ == "column" and name == "embedding" and object.table.name == "topics")


engine = migration_engine(settings.database_url)

with engine.connect() as connection:
    context.configure(
        connection=connection, target_metadata=Base.metadata, include_object=include_object
    )

    with context.begin_transaction():
        context.run_migrations()
