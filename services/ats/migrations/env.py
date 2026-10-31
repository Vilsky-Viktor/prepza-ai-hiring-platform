from logging.config import fileConfig

from alembic import context
from testee_common.db.db import migration_engine

import ats.models.ats
import ats.models.outbox  # noqa: F401
from ats.config import settings
from ats.models.base import Base

fileConfig(context.config.config_file_name)

engine = migration_engine(settings.database_url)

with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata)

    with context.begin_transaction():
        context.run_migrations()
