from prepza_common.db.db import database

from generation.config import settings
from generation.constants.db import DB_MAX_OVERFLOW, DB_POOL_SIZE

engine, Session = database(settings.database_url, DB_POOL_SIZE, DB_MAX_OVERFLOW)
