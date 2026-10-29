from logging.config import fileConfig

from alembic import context
from prepza_common.db.db import migration_engine

import rounds.models.answers  # registers the tables on Base.metadata
import rounds.models.outbox
import rounds.models.sessions
import rounds.models.signals  # noqa: F401
from rounds.config import settings
from rounds.models.base import Base

fileConfig(context.config.config_file_name)

engine = migration_engine(settings.database_url)

with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata)

    with context.begin_transaction():
        context.run_migrations()
