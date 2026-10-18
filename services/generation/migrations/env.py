from logging.config import fileConfig

from alembic import context
from prepza_common.db import sqlalchemy_url
from sqlalchemy import create_engine

import app.models.generation  # registers the tables on Base.metadata
import app.models.key_checks
import app.models.outbox
import app.models.patterns  # noqa: F401
from app.config.settings import settings
from app.models.base import Base

fileConfig(context.config.config_file_name)

engine = create_engine(sqlalchemy_url(settings.database_url))

with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata)

    with context.begin_transaction():
        context.run_migrations()
