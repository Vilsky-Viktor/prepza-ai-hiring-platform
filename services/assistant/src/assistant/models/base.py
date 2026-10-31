from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase
from testee_common.config.constants import NAMING_CONVENTION


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
