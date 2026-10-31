from testee_common.db.db import database

from site_content.config import settings
from site_content.constants.db import DB_MAX_OVERFLOW, DB_POOL_SIZE

engine, Session = database(settings.database_url, DB_POOL_SIZE, DB_MAX_OVERFLOW)
