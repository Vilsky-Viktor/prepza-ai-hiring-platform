from logging.config import fileConfig

from alembic import context
from testee_common.db.db import migration_engine

import assistant.models.conversations
import assistant.models.help_votes
import assistant.models.oauth
import assistant.models.updates  # noqa: F401
from assistant.config import settings
from assistant.models.base import Base

fileConfig(context.config.config_file_name)

engine = migration_engine(settings.database_url)

with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata)

    with context.begin_transaction():
        context.run_migrations()
