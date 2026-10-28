from prepza_common.config.constants import NAMING_CONVENTION
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
