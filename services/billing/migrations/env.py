from logging.config import fileConfig

from alembic import context
from prepza_common.db.db import migration_engine

import billing.models.billing
import billing.models.limits
import billing.models.outbox
import billing.models.usage  # noqa: F401
from billing.config import settings
from billing.models.base import Base

fileConfig(context.config.config_file_name)

engine = migration_engine(settings.database_url)

with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata)

    with context.begin_transaction():
        context.run_migrations()
