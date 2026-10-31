from logging.config import fileConfig

from alembic import context
from testee_common.db.db import migration_engine

import accounts.models.emails  # registers the tables on Base.metadata
import accounts.models.erasures
import accounts.models.legal
import accounts.models.outbox  # noqa: F401
from accounts.config import settings
from accounts.models.base import Base

fileConfig(context.config.config_file_name)

engine = migration_engine(settings.database_url)

with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata)

    with context.begin_transaction():
        context.run_migrations()
