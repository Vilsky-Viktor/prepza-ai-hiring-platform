from logging.config import fileConfig

from alembic import context
from prepza_common.db import sqlalchemy_url
from sqlalchemy import create_engine

import app.models.bulk
import app.models.campaigns
import app.models.notifications
import app.models.opt_outs
import app.models.outbox
import app.models.sent_emails
import app.models.slack
import app.models.suppressed  # noqa: F401
from app.config.settings import settings
from app.models.base import Base

fileConfig(context.config.config_file_name)


def include_name(name, type_, parent_names):
    """legal_notices has no model since bulk sends replaced it (migration 0009), but stays until
    no running version reads it: autogenerate leaves it alone."""

    return not (type_ == "table" and name == "legal_notices")


engine = create_engine(sqlalchemy_url(settings.database_url))

with engine.connect() as connection:
    context.configure(
        connection=connection, target_metadata=Base.metadata, include_name=include_name
    )

    with context.begin_transaction():
        context.run_migrations()
