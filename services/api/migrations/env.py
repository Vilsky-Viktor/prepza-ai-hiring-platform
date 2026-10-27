from logging.config import fileConfig

from alembic import context
from prepza_common.db.db import migration_engine

import api.models.api
import api.models.outbox  # noqa: F401
from api.config import settings
from api.models.base import Base

fileConfig(context.config.config_file_name)

engine = migration_engine(settings.database_url)

with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata)

    with context.begin_transaction():
        context.run_migrations()
