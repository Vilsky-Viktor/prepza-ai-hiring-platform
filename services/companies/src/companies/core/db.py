from prepza_common.db.db import database

from companies.config import settings

engine, Session = database(settings.database_url)
