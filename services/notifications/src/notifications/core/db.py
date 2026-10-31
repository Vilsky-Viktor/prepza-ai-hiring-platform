from testee_common.db.db import database

from notifications.config import settings
from notifications.constants.notifications import DB_MAX_OVERFLOW, DB_POOL_SIZE

engine, Session = database(settings.database_url, DB_POOL_SIZE, DB_MAX_OVERFLOW)
