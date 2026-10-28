from logging.config import fileConfig

from alembic import context
from prepza_common.db.db import migration_engine

import notifications.models.bulk
import notifications.models.campaigns
import notifications.models.notifications
import notifications.models.opt_outs
import notifications.models.outbox
import notifications.models.sent_emails
import notifications.models.slack
import notifications.models.soft_bounces
import notifications.models.suppressed  # noqa: F401
from notifications.config import settings
from notifications.models.base import Base

fileConfig(context.config.config_file_name)


def include_name(name, type_, parent_names):
    """legal_notices has no model since bulk sends replaced it (migration 0009), but stays until
    no running version reads it: autogenerate leaves it alone."""

    return not (type_ == "table" and name == "legal_notices")


engine = migration_engine(settings.database_url)

with engine.connect() as connection:
    context.configure(
        connection=connection, target_metadata=Base.metadata, include_name=include_name
    )

    with context.begin_transaction():
        context.run_migrations()
