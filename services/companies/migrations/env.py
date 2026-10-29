from logging.config import fileConfig

from alembic import context
from prepza_common.db.db import migration_engine

import companies.models.audit
import companies.models.companies
import companies.models.events
import companies.models.interview_notes
import companies.models.interview_results
import companies.models.interviews
import companies.models.invites
import companies.models.outbox
import companies.models.removals  # noqa: F401
from companies.config import settings
from companies.models.base import Base

fileConfig(context.config.config_file_name)

engine = migration_engine(settings.database_url)

with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata)

    with context.begin_transaction():
        context.run_migrations()
