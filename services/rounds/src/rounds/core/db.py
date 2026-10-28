from prepza_common.db.db import database

from rounds.config import settings

engine, Session = database(settings.database_url)
