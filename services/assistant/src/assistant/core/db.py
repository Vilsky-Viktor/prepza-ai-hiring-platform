from prepza_common.db.db import database

from assistant.config import settings
from assistant.constants.assistant import DB_MAX_OVERFLOW, DB_POOL_SIZE

engine, Session = database(settings.database_url, DB_POOL_SIZE, DB_MAX_OVERFLOW)
