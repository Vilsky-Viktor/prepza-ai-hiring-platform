from logging.config import fileConfig

from alembic import context
from prepza_common.db.db import migration_engine

import site_content.models.news  # registers the tables on Base.metadata
import site_content.models.outbox  # noqa: F401
from site_content.config import settings
from site_content.models.base import Base

fileConfig(context.config.config_file_name)

engine = migration_engine(settings.database_url)

with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata)

    with context.begin_transaction():
        context.run_migrations()
