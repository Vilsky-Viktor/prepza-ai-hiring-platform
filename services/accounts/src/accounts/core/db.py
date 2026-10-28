from prepza_common.db.db import database

from accounts.config import settings
from accounts.constants.db import DB_MAX_OVERFLOW, DB_POOL_SIZE

engine, Session = database(settings.database_url, DB_POOL_SIZE, DB_MAX_OVERFLOW)
